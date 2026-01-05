#!/usr/bin/env python3

import socket
import sys
import argparse
import demos_config
from typing import Sized
import numpy as np
import msgpack
import random
import time

CYCLES = 20
SLEEP_TIME = 1
INJECTIONS = 2

PORT = 8083
HOST = None
MODEL = None
CONFIG = None

def srv_connect(host: str, model: int, config: int) -> bytearray:

    # get the model-configuration-based trajectory 
    demo_fname = f"sign_M{model}_C{config}_trajectory"
    demo_func = getattr(demos_config, demo_fname)
    trajectory = demo_func(CYCLES)
    payload = msgpack.packb(trajectory)    # prepare the trace
    try:
        # Create TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[*] Connecting to {host}:{PORT}...", file=sys.stderr)
        # Connect to server
        sock.connect((host, PORT))
        print(f"[+] Connected successfully!", file=sys.stderr)
        # Send the initial trajectory
        if isinstance(payload, Sized):
            sock.sendall(len(payload).to_bytes(4, 'big'))
            sock.sendall(payload)
        else:
            print("Error with payload type")
            exit(1)
        # wait for simulation started ack
        response = sock.recv(64)
        print(response.decode('utf-8'))
        # Send a couple of perturbations
        TIME_OFFSET = 0
        for ITERNO in range(INJECTIONS):
            # inject a perturbation
            PERIOD = CYCLES // 2
            # get the model-configuration-based perturbation
            demo_fname = f"sign_M{model}_C{config}_perturbation"
            demo_func = getattr(demos_config, demo_fname)
            perturbation = demo_func(PERIOD, ITERNO)
            payload = msgpack.packb(perturbation)
            if isinstance(payload, Sized):
                sock.sendall(len(payload).to_bytes(4, 'big'))
                sock.sendall(payload)
            else:
                print("Error with payload type")
                exit(1)
            # wait for ack
            response = sock.recv(64)
            print(response.decode('utf-8'))
            TIME_OFFSET += PERIOD
            # random sleep (between 1 and 6 seconds)
            time.sleep(random.randint(1, PERIOD // 2))
        # wait for final response
        response = sock.recv(64)        
        # Close the socket
        sock.close()
        return bytearray(response)
    except ConnectionRefusedError:
        return bytearray(f"ERROR: Connection refused by {host}:{PORT}".encode('utf-8'))
    except socket.gaierror as e:
        return bytearray(f"ERROR: Could not resolve hostname '{host}': {e}".encode('utf-8'))
    except Exception as e:
        return bytearray(f"ERROR: {type(e).__name__}: {e}".encode('utf-8'))

def main():
    parser = argparse.ArgumentParser(
        description="Connect to the simulation server via TCP",
    )
    parser.add_argument('host', help='Server hostname or IP address')
    parser.add_argument('model', help='Model id')
    parser.add_argument('config', help='Config id')        
    
    args = parser.parse_args()
    HOST = args.host
    MODEL = args.model
    CONFIG = args.config

    print(f"host:\t{HOST}")
    print(f"model:\t{MODEL}")
    print(f"config:\t{CONFIG}")
    
    result = srv_connect(HOST, MODEL, CONFIG)

    print(result.decode('utf-8'))

if __name__ == "__main__":
    main()
