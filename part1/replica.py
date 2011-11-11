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
        propose_N, propose_v = v[3], v[4]
        if self.db["N"] <= propose_N:
          self.db["N"] = propose_N
          self.db["V"] = propose_v
        else:
          pass
          # what now? TODO
        out.append(None)
      else:
        out.append(None)

      cv.notify()
      cv.release()

  def prepare(self, N):
    cv = threading.Condition()
    cv.acquire()
    res = []
    self.queue.put((cv, "prepare", res, N))
    while len(res) < 1:
      cv.wait()
    cv.release()
    return res[0]

  def accept(self, N, v):
    cv = threading.Condition()
    cv.acquire()
    res = []
    self.queue.put((cv, "accept", res, N, v))
    while len(res) < 1:
      cv.wait()
    cv.release()
    return res[0]

class learner(threading.Thread):
  def __init__(self, peers):
    threading.Thread.__init__(self)
    self.peers = peers
    self.queue = queue.Queue()
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
      maj = False

      # Phase 1:
      N = 0
      maj, resps = zmqrpc.async_multicall(self.peers, 0.1, "prepare", [N])

      if maj:
        # We can only send our 'v' for acceptance if we have not crossed the
        # rubicon: if any other v *possibly* has quorum, we can't submit.
        prev_vs = []
        for (promise, N, prev_v) in resps:
          found = False
          for rec in prev_vs:
            if rec[0] == prev_v:
              rec[1] += 1
              found = True
          if not found:
            prev_vs.append([prev_v, 1])

        for (prev_v, count) in prev_vs:
          if count >= ((len(self.peers) // 2) + 1):  # quorum?
            if prev_v is not None:
              v = prev_v
            break

        # Phase 2:
        zmqrpc.async_multicall(self.peers, 0.1, "accept", [N, v])

      else:  # we can't submit if we didn't get a response from majority of peers
        pass

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
