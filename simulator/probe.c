// go:build ignore

#include "headers/vmlinux.h"

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

// spec values
volatile const __u64 ADDR_BASE;
volatile const __u64 ADDR_OBJ;
volatile const __u64 ADDR_DREL;
volatile const __u64 OFFSET_MAJORT;

// timing
volatile const __u32 MINOR_TO_MAJOR_RATIO;
__u32 minor_step = 0;
__u32 cycle = 0;
volatile const __u32 MAX_CYCLES;

// signals
const __u16 SIGKILL = 9;

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
	}
	if (isMajor) {
		// overwrite userspace memory
		// todo add
	}

	

	// todo overwrite value
	/* // overwriting a memory location of a process executing a simulink model */
        /* __s64 val_to_write = 0; */
	/* err = bpf_probe_write_user((void *)(ADDR_BASE+ADDR_OBJ+ADDR_DREL), &val_to_write, sizeof(val_to_write)); */
	/* if (err != 0) { */
	/* 	bpf_printk("UWRITE FAILED: %ld\n", err); */
	/* 	return 0; */
        /* } else { */
	/* 	bpf_printk("d_rel overwritten\n"); */
        /* } */
	
	return 0;
}

char __license[] SEC("license") = "Dual MIT/GPL";
