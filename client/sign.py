#!/usr/bin/env python3

import socket
import sys
import argparse
from typing import Sized
import numpy as np
import msgpack
import random
import time

PORT = 8083
CYCLES = 20
SLEEP_TIME = 1
INJECTIONS = 2

def srv_connect(host: str) -> bytearray:

    X = np.array([10 + 0.0001 * (i + 1) for i in range(CYCLES)], dtype=np.float64)
    Y = np.array([20 for _ in range(CYCLES)], dtype=np.float64)
    trajectory = dict()
    trajectory["X"] = X.tolist()
    trajectory["Y"] = Y.tolist()
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
        for iterno in range(INJECTIONS):
            # inject a perturbation
            PERIOD = CYCLES // 2
            X = np.array([0.001 * (i + 1) for i in range(PERIOD)], dtype=np.float64)
            Y = np.array([0.02 for _ in range(PERIOD)], dtype=np.float64)
            PERIOD_START = 0 if iterno == 0 else random.randint(0, PERIOD // 2)
            time_trace = [PERIOD_START + i for i in range(PERIOD // 2)]
            perturbation = dict()
            perturbation["X"] = X.tolist()
            perturbation["Y"] = Y.tolist()
            perturbation["time"] = np.array(time_trace, dtype=np.uint32).tolist()
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
    
    args = parser.parse_args()
    
    print(srv_connect(args.host).decode('utf-8'))

if __name__ == "__main__":
    main()
