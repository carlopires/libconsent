#!/usr/bin/python3 -tt

# Conrad Meyer <cemeyer@uw.edu>
# 0824410
# CSE 550 Problem Set 3
# Thu Nov 10 2011

import queue
import sys
import threading
import time
import zmq
import zmqrpc

class acceptor(threading.Thread):
  def __init__(self, peers):
    threading.Thread.__init__(self)
    self.peers = peers
    self.daemon = True
    self.start()

  def run(self):
    pass # TODO

class learner(threading.Thread):
  def __init__(self, peers):
    threading.Thread.__init__(self)
    self.peers = peers
    self.daemon = True
    self.start()

  def run(self):
    pass # TODO

  def value(self):
    pass # TODO

class proposer(threading.Thread):
  def __init__(self, peers):
    threading.Thread.__init__(self)
    self.peers = peers
    self.queue = queue.Queue()
    self.daemon = True
    self.start()

  def propose(self, value):
    self.queue.put(value)

  def run(self):
    while True:
      v = self.queue.get()
      XXX # TODO

class rpcsurface:
  def __init__(self, peers):
    self.learner = learner(peers)
    self.acceptor = acceptor(peers)
    self.proposer = proposer(peers)

  def propose(self, value):
    self.proposer.propose(value)
    return None

  def learn(self):
    return self.learner.value()

def usage():
  print("Usage:")
  print("  replica.py <filename.db> <myaddr> <peers>")
  print()
  print("filename.db - Local file to use as the durable storage for paxos")
  print("myaddr      - The zmq endpoint to use for this node")
  print("peers       - Comma delimited list of zmq endpoints for acceptor peers")

def main(args):
  if len(args) < 3:
    usage()
    sys.exit(1)

  db, myaddr, peers = args[:3]
  peers = peers.split(",")

  zctx = zmq.Context()

  peerrpcs = [zmqrpc.Client(zctx, x) for x in peers]
  server = zmqrpc.Server(zctx, myaddr, rpcsurface(peerrpcs))
  server.join()

if __name__ == "__main__":
  try:
    main(sys.argv[1:])
  except KeyboardInterrupt:
    print(" Shutting down.")
