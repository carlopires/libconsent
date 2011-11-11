#!/usr/bin/python3 -tt

import sys
import zmq
import zmqrpc

def main(args):
  zctx = zmq.Context()

  client = zmqrpc.Client(zctx, args[1])
  print(getattr(client, args[2])(*args[3:]))

def usage():
  print("Usage: rpc_debug.py zmq://endpoint rpc_name arg1 arg2 ...")

if len(sys.argv) < 3:
  usage()
  sys.exit(1)
else:
  main(sys.argv)
