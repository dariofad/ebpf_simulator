# Setup

- create a local file named `.BIN_PATH` containing the path of the
  `DualACC` binary you just built (e.g.,
  `/home/user/sim2cpp/DualACCC/dualACC`)
- create a local file named `.BIN_SYM` containing the mangled name of
  the `egoCar::step()` function of the `DualACC` (e.g.,
  `_ZN6egoCar4stepEv`), you can get the name by looking at the binary
  symbols with `objdump -t dualACC`
- create a local file named `.ADDRS.json` listing the base addresses
  we are monitoring, it should look like the following
```
{
    "ADDR_DREL": "55555556e350",
    "ADDR_AEGO": "55555556e368",
    "ADDR_VEGO": "55555556e360",
    "OFFSET_STEP": "418",
    "OFFSET_MAIN": "188",
    "MINOR_TO_MAJOR_RATIO": "3"
}
```
To get obtain these addresses you can use GDB:
1. Disable ASLR
2. Go to the `DualACC` folder
3. Run `gdb dualACC`, then follow the next steps
4. `b main`
5. `r`
6. `p &ego.egoCar_Y.d_rel`, the value you get is `ADDR_DREL`
7. `p &ego.egoCar_Y.a_ego`, the value you get is `ADDR_AEGO`
8. `p &ego.egoCar_Y.v_ego`, the value you get is `ADDR_VEGO`
9. `info line egoCar.cpp:2300`, this is the value of `OFFSET_STEP`
10. `info line main.cpp:28`, this is the value of `OFFSET_MAIN`
11. `q`, to quit GDB
