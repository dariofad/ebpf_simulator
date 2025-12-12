#!/usr/bin/env python3

import json
import sys
from typing import OrderedDict

config = json.load(sys.stdin)
TABLE = OrderedDict()
NOF_WI, NOF_RI, NOF_RO = 0, 0, 0
WRITE_TIMING_I =  config["WRITE_TIMING_I"]
READ_TIMING_I =  config["READ_TIMING_I"]
READ_TIMING_O =  config["READ_TIMING_O"]

def summarize_signals(signals, offset=0):

    for pos, sign in enumerate(signals):
        sign_name = sign["SIGN_NAME"]
        if TABLE.get(sign_name, -1) == -1:
            TABLE[sign_name] = [pos+offset]
        else:
            TABLE[sign_name].append(pos+offset)

if WRITE_TIMING_I:
    summarize_signals(WRITE_TIMING_I["SIGNALS"])
    NOF_WI = len(WRITE_TIMING_I["SIGNALS"])
if READ_TIMING_I:
    summarize_signals(READ_TIMING_I["SIGNALS"], NOF_WI)
    NOF_RI = len(READ_TIMING_I["SIGNALS"])    
if READ_TIMING_O:
    summarize_signals(READ_TIMING_O["SIGNALS"], NOF_WI + NOF_RI)
    NOF_RO = len(READ_TIMING_O["SIGNALS"])        

print("SIGNAL RECAP:")
max_sign_name_len = max([len(n) for n in TABLE.keys()]) + 1
for sign_name in TABLE.keys():
    snames = str(TABLE[sign_name])
    rjust_rx = snames.rjust(12)
    ljust_sx = (sign_name + ":").ljust(max_sign_name_len)
    print(f"\t{ljust_sx}{rjust_rx}")
