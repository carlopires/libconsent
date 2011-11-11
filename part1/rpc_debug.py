#!/usr/bin/python3 -tt

import sys
import zmq
import zmqrpc

zctx = zmq.Context()

client = zmqrpc.Client(zctx, sys.argv[1])
print(getattr(client, sys.argv[2])(*sys.argv[3:]))
