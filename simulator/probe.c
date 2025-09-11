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

// d_rel map
struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__type(key, __u32);
	__type(value, __u64); // use a u64 to store a double value
} d_rel_map SEC(".maps");

// a_ego map
struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__type(key, __u32);
	__type(value, __u64); // use a u64 to store a double value
} a_ego_map SEC(".maps");

// v_ego map
struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__type(key, __u32);
	__type(value, __u64); // use a u64 to store a double value
} v_ego_map SEC(".maps");


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
		// read d_rel from input trace
		__u64 *d_rel = bpf_map_lookup_elem(&d_rel_map, &d_rel_key);
		if (!d_rel){
			bpf_printk("Error reading d_rel");
			return -1;
		}
		bpf_printk("d_rel at idx %d: %llu", d_rel_key, *d_rel);
		// overwrite d_rel in userspace memory
		long err = bpf_probe_write_user((void *)(ADDR_DREL), d_rel, 8);
		if (err != 0) {
			bpf_printk("UWRITE FAILED (d_rel_i): %ld\n", err);
			return -1;
		}	
		__u64 buf = 0;
		// check value written in userspace
		if (bpf_probe_read_user(&buf, sizeof(buf), (void *)(ADDR_DREL)) == 0) {
			bpf_printk("Read after write: %llu\n", buf);
		} else {
			bpf_printk("Failed to read");
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
		bpf_printk("a_ego: %llu\n", buf);
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
		bpf_printk("v_ego: %llu\n", buf);
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
		bpf_printk("Written v_ego: %llu", buf);
	}

	return 0;
}


char __license[] SEC("license") = "Dual MIT/GPL";
