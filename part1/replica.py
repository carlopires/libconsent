#!/usr/bin/python3 -tt

# Conrad Meyer <cemeyer@uw.edu>
# 0824410
# CSE 550 Problem Set 3
# Thu Nov 10 2011

import queue
import shelve
import sys
import threading
import time
import zmq
import zmqrpc

# Takes in a number of peers, and a list of at most n_peers values.
# Returns (True, value) if any value has quorum.
# Returns (False, None) if no value has quorum.
def majority(n_peers, values):
  if len(values) < ((n_peers // 2) + 1):
    return (False, None)

  v_counts = []
  for v in values:
    found = False
    for rec in v_counts:
      if rec[0] == v:
        rec[1] += 1
        found = True
    if not found:
      v_counts.append([v, 1])

  for (v, count) in v_counts:
    if count >= ((n_peers // 2) + 1):  # quorum?
      return (True, v)

  return (False, None)

class acceptor(threading.Thread):
  def __init__(self, peers, dbfile):
    threading.Thread.__init__(self)
    self.peers = peers
    self.queue = queue.Queue()
    self.daemon = True
    self.db = shelve.open(dbfile)
    self.start()

  def run(self):
    while True:
      v = self.queue.get()
      cv, cmd, out = v[0], v[1], v[2]
      cv.acquire()

      if cmd == "prepare":
        # Phase 1:
        propose_N = v[3]
        if "N" not in self.db or propose_N > self.db["N"]:
          self.db["N"] = propose_N
          out.append(("promise", propose_N, self.db.get("V")))
        else:
          pass
          # what now? TODO
      elif cmd == "accept":
        # Phase 2:
        propose_N, propose_v = v[3]
        if "N" not in self.db or self.db["N"] <= propose_N:
          self.db["N"] = propose_N
          self.db["V"] = propose_v
        else:
          pass
          # what now? TODO
        out.append(None)
      elif cmd == "query":
        out.append((self.db.get("N"), self.db.get("V")))
      else:
        out.append(None)

      cv.notify()
      cv.release()

  class _WorkFuture:
    def __init__(self, queue, cmd, args):
      self.cv = threading.Condition()
      self.cv.acquire()
      self.res = []
      queue.put((self.cv, cmd, self.res, args))

    def get(self):
      while len(self.res) < 1:
        self.cv.wait()
      self.cv.release()
      return self.res[0]

  def prepare(self, N):
    return acceptor._WorkFuture(self.queue, "prepare", N).get()

  def accept(self, N, v):
    return acceptor._WorkFuture(self.queue, "accept", (N, v)).get()

  def query(self):
    return acceptor._WorkFuture(self.queue, "query", None).get()

class learner(threading.Thread):
  def __init__(self, peers):
    threading.Thread.__init__(self)
    self.peers = peers
    self.queue = queue.Queue()
    self.daemon = True
    self.timeout = 0.1
    self.start()

  def run(self):
    pass

  def value(self):
    maj, resps = zmqrpc.async_multicall(self.peers, self.timeout, "query", [])
    maj, maj_val = majority(len(self.peers), [resp[1] for resp in resps])
    if maj and maj_val is not None:
      return ("KNOW", maj_val)
    else:
      return ("DONT_KNOW",)

class proposer(threading.Thread):
  def __init__(self, peers):
    threading.Thread.__init__(self)
    self.peers = peers
    self.queue = queue.Queue()
    self.daemon = True
    self.timeout = 0.1  # seconds
    self.start()

  def propose(self, value):
    self.queue.put(value)

  def run(self):
    while True:
      v = self.queue.get()
      maj = False

      # Phase 1:
      N = 0
      maj, resps = zmqrpc.async_multicall(self.peers, self.timeout, "prepare", [N])

      if maj:
        # We can only send our 'v' for acceptance if we have not crossed the
        # rubicon: if any other v *possibly* has quorum, we can't submit.
        maj, maj_val = majority(len(self.peers), [resp[2] for resp in resps])

      if maj:
        if maj_val is not None:
          v = maj_val

        # Phase 2:
        zmqrpc.async_multicall(self.peers, self.timeout, "accept", [N, v])

class rpcsurface:
  def __init__(self, peers, dbfile):
    self.learner = learner(peers)
    self.acceptor = acceptor(peers, dbfile)
    self.proposer = proposer(peers)

  def propose(self, value):
    self.proposer.propose(value)
    return None

  def learn(self):
    return self.learner.value()

  def accept(self, N, v):
    return self.acceptor.accept(N, v)

  def prepare(self, N):
    return self.acceptor.prepare(N)

  def query(self):
    return self.acceptor.query()

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
  server = zmqrpc.Server(zctx, myaddr, rpcsurface(peerrpcs, db))
  server.join()

if __name__ == "__main__":
  try:
    main(sys.argv[1:])
  except KeyboardInterrupt:
    print(" Shutting down.")
