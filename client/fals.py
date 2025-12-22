#!/usr/bin/env python3

from typing import Sized
import argparse
import demos_config
import msgpack
import socket
import sys

PORT = 8081
HOST = None
MODEL = None
CONFIG = None

def srv_connect(host: str, model: int, config: int) -> bytearray:

    # get the model-configuration-based trajectory 
    demo_fname = f"fals_M{model}_C{config}_trajectory"
    demo_func = getattr(demos_config, demo_fname)
    trajectory = demo_func()
    # serialize the trajectory with msgpack
    payload = msgpack.packb(trajectory)

    try:
        # Create TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[*] Connecting to {host}:{PORT}...", file=sys.stderr)
        # Connect to server
        sock.connect((host, PORT))
        print(f"[+] Connected successfully!", file=sys.stderr)
        # Send the trajectory to the server
        if isinstance(payload, Sized):
            sock.sendall(len(payload).to_bytes(4, 'big'))
            sock.sendall(payload)
        else:
            print("Error with payload type")
            exit(1)
        # Receive response size
        response = sock.recv(4)
        resp_len = int.from_bytes(response, byteorder='big')
        print(f"[*] Receiving a {resp_len}-byte response")
        data = bytearray()
        bytes_received = 0
        while bytes_received < resp_len:
            chunk = sock.recv(resp_len - bytes_received)
            if not chunk:  # Peer closed the connection
                raise EOFError("Socket connection closed before all bytes were received")
            data.extend(chunk)
            bytes_received += len(chunk)
        # Close the socket
        sock.close()
        return data
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
    unpacked_res = msgpack.unpackb(result)
    print("(...first 15 output trace records)")
    for sign in unpacked_res['OUT_SIGNALS']:
        print(sign['SIGN_NAME'])
        print(*(sign['VALUES'][:15]), "...")        

if __name__ == "__main__":
    main()
