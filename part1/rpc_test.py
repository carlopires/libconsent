#!/usr/bin/python3 -tt

import sys
import time
import zmq
import zmqrpc

zctx = zmq.Context()

class rpc:
  def __init__(self, delay):
    self.delay = delay
    self.it = -1

  def respond(self):
    time.sleep(self.delay)
    self.it += 1
    return (self.it, self.delay)

servers = [zmqrpc.Server(zctx, "inproc://XXX%d" % n, rpc(n)) for n in range(3)]
clients = [zmqrpc.Client(zctx, "inproc://XXX%d" % n) for n in range(3)]

for i in [0.9, 1.1, 1.9, 2.1]:
  print(i, zmqrpc.async_multicall(clients, i, "respond", []))
