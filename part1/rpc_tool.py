#!/usr/bin/python3 -tt

# Conrad Meyer <cemeyer@uw.edu>
# 0824410
# CSE 550 Problem Set 3
# Thu Nov 10 2011

import sys
import zmq
import zmqrpc

def main(args):
  zctx = zmq.Context()

  client = zmqrpc.Client(zctx, args[1])
  print(getattr(client, args[2])(*args[3:]))

def usage():
  print("Usage: rpc_tool.py <url://replica> <call_name> [arg1 [arg2 [...]]]")

if len(sys.argv) < 3:
  usage()
  sys.exit(1)
else:
  main(sys.argv)
