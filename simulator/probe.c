// go:build ignore

#include "headers/vmlinux.h"

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

// spec values
volatile const __u64 ADDR_DREL;
volatile const __u64 ADDR_AEGO;
volatile const __u64 ADDR_VEGO;

// timing
volatile const __u32 MINOR_TO_MAJOR_RATIO;
__u32 minor_step = 0;
__u32 cycle = 0;
volatile const __u32 MAX_CYCLES;

// signals
const __u16 SIGKILL = 9;

// d_rel_noise map
struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__type(key, __u32);
	__type(value, __u64); // use __u64 to store an ieee754 value
} d_rel_noise_map SEC(".maps");

// a_ego map
struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__type(key, __u32);
	__type(value, __u64); // use __u64 to store an ieee754 value
} a_ego_map SEC(".maps");

// v_ego map
struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__type(key, __u32);
	__type(value, __u64); // use __u64 to store an ieee754 value
} v_ego_map SEC(".maps");

static __always_inline int count_leading_left_zeroes(__u64 n) {

	int count = 0;
	if (n == 0) {
		return 64;
	}
	if ((n >> 32) == 0) {
		count += 32;
		n <<= 32;
	}
	if ((n >> 48) == 0) {
		count += 16;
		n <<= 16;
	}
	if ((n >> 56) == 0) {
		count += 8;
		n <<= 8;
	}
	if ((n >> 60) == 0) {
		count += 4;
		n <<= 4;
	}
	if ((n >> 62) == 0) {
		count += 2;
		n <<= 2;
	}
	if ((n >> 63) == 0) {
		count += 1;
	}
	return count;
}

// Returns always 0 in case of overflow, also prints a message to trace_pipe
static __u64 ieee754_add(__u64 a, __u64 b) {
	
	__u64 s_a = (a >> 63) & 1;
	__u64 s_b = (b >> 63) & 1;
    
	__u64 e_a = (a >> 52) & 0x7ff;
	__u64 m_a = a & 0x000fffffffffffffULL;
	if (e_a != 0) {
		m_a |= (1ULL << 52); // non-zero value, explicitly add the first "mantissa bit"
	}

	__u64 e_b = (b >> 52) & 0x7ff;
	__u64 m_b = b & 0x000fffffffffffffULL;
	if (e_b != 0) {
		m_b |= (1ULL << 52);
	}

	bool same_sign = (s_a == s_b);

	// determine the large and small number
	bool a_l = (e_a > e_b) || ((e_a == e_b) && (m_a > m_b));
	__u64 e_l, e_s, m_l, m_s;
	__u64 s_l, s_s;
	if (a_l) {
		e_l = e_a;
		m_l = m_a;
		s_l = s_a;
		e_s = e_b;
		m_s = m_b;
		s_s = s_b;
	} else {
		e_l = e_b;
		m_l = m_b;
		s_l = s_b;
		e_s = e_a;
		m_s = m_a;
		s_s = s_a;
	}

	// align the two mantissa to perform the operation
	__s32 delta = (__s32)e_l - (__s32)e_s;
	if (delta > 63) {
		delta = 63;  // undefined behavior
	}
	m_s >>= delta;

	__u64 m_res;
        __u64 s_res = s_l;
        if (same_sign) {
                m_res = m_l + m_s;
        } else {
                m_res = m_l - m_s;
        }
        if (m_res == 0) {
                return 0ULL;
        }

        // normalize the representation of the result (A + B)
        // A. fix the exponent
        int left_zeros = count_leading_left_zeroes(m_res);
        int msb_pos = 63 - left_zeros;
        int shift = msb_pos - 52;
        __s32 e_res = (__s32)e_l + shift;

        // overflow occurred
	if (e_res > 2046 || e_res < 0) {
		bpf_printk("OP RESULTED IN OVERFLOW");
		return 0ULL;
	}
	
        // B. shift mantissa accordingly
        if (shift > 0) {
                if (shift > 63)
                  shift = 63;
                m_res >>= shift;
        } else if (shift < 0) {
                int left_shift = -shift;
                if (left_shift > 63)
                  left_shift = 63;
                m_res <<= left_shift;
        }

        // mask mantissa
        __u64 mant = m_res & ((1ULL << 52) - 1ULL);

        // assemble the result
        __u64 result = (s_res << 63) | ((__u64)e_res << 52) | mant;
	
        return result;
}

static __u64 ieee754_sub(__u64 a, __u64 b) {

	// flip sign and do an addition
	b ^= (1ULL << 63);
	return ieee754_add(a, b);
}

SEC("uretprobe/drel_probe")
int uprobe_drel_probe() {

	// determine if the call is part of a major cycle
	bool isMajor = 0;
	if (minor_step % MINOR_TO_MAJOR_RATIO == 0){
		isMajor = 1;
		cycle++;		
	}
	minor_step++;	
	if (cycle > MAX_CYCLES) {
		bpf_printk("SIGKILL sent to process");
		bpf_send_signal(SIGKILL);
		return 0;
	}
        if (isMajor) {
		__u32 d_rel_key = cycle - 1;
		// 1. read d_rel from input trace
		__u64 *d_rel_noise = bpf_map_lookup_elem(&d_rel_noise_map, &d_rel_key);
		if (!d_rel_noise){
			bpf_printk("Error reading d_rel_noise");
			return -1;
		}
		
		// 2. read d_rel from user space
		__u64 d_rel = 0;
		if (bpf_probe_read_user(&d_rel, sizeof(d_rel), (void *)(ADDR_DREL)) == 0) {
			bpf_printk("d_rel from uspace: %llu", d_rel);
		} else {
			bpf_printk("Failed to read");
			return -1;
		}

		// 3. add noise to d_rel
		d_rel = ieee754_add(d_rel, *d_rel_noise);
		bpf_printk("d_rel_noise: %llu", *d_rel_noise);		
		bpf_printk("new d_rel: %llu", d_rel);		

		// 4. overwrite d_rel value in user space
		long err = bpf_probe_write_user((void *)(ADDR_DREL), &d_rel, 8);
		if (err != 0) {
			bpf_printk("UWRITE FAILED (d_rel_i): %ld", err);
			return -1;
		}	
	}

	return 0;
}

SEC("uretprobe/output_probe")
int uprobe_output_probe() {

	__u32 write_map_key = cycle - 1;	

	__u64 buf = 0;
	// read a_ego
	if (bpf_probe_read_user(&buf, sizeof(buf), (void *)(ADDR_AEGO)) == 0) {
		bpf_printk("a_ego: %llu", buf);
	} else {
		bpf_printk("Failed to read a_ego");
		return -1;
	}
	// write it to the map
	int err = bpf_map_update_elem(&a_ego_map, &write_map_key, &buf, BPF_ANY);
	if (err != 0) {
		bpf_printk("Cannot write a_ego to its map");
		return -1;
	} else {
		bpf_printk("Written a_ego: %llu", buf);
	}
	
	// read v_ego
	if (bpf_probe_read_user(&buf, sizeof(buf), (void *)(ADDR_VEGO)) == 0) {
		bpf_printk("v_ego: %llu", buf);
	} else {
		bpf_printk("Failed to read v_ego");
		return -1;
	}
	// write it to the map
	err = bpf_map_update_elem(&v_ego_map, &write_map_key, &buf, BPF_ANY);
	if (err != 0) {
		bpf_printk("Cannot write v_ego to its map");
		return -1;
	} else {
		bpf_printk("Written v_ego: %llu\n", buf);
	}

	return 0;
}


char __license[] SEC("license") = "Dual MIT/GPL";
