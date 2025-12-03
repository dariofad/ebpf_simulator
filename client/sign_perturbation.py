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

def srv_connect(host: str) -> bytearray:

    X = np.array([1+float(i)/100 for i in range(100)], dtype=np.float64)
    Y = np.array([2 for _ in range(100)], dtype=np.float64)
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
        for iterno in range(2):
            # random sleep (between 1 and 6 seconds)
            time.sleep(random.randint(1, 6))
            # inject a perturbation
            period = 15
            X = np.array([1+float(i)/100 for i in range(period)], dtype=np.float64)
            Y = np.array([2.8 for _ in range(period)], dtype=np.float64)
            period_start = random.randint(0, 20)
            time_trace = [min((iterno + 1) * period + period_start + i, 99)
                          for i in range(period)]
            perturbation = dict()
            perturbation["X"] = X.tolist()
            perturbation["Y"] = Y.tolist()
            perturbation["time"] = time_trace
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
