# Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
#
# This work is placed under the MIT license, the full text of which is
# included in the `COPYING' file at the root of the project sources.
#
# Author(s): Conrad Meyer

# Wire protocol (borrowed from "Paxos made code"):
#   Prepare: (i, b)
#   Promise: (i, b, V, VB)
#   Accept: (i, b, v)
#   Learn: (i, b, v)
#
# Acceptor stable storage:
#   iid -> (B, V, VB)

import queue
import threading
import time
import zmq

from libconsent import asyncrpc

def _majority(n_peers, values):
  """
  Takes in a number of peers, and a list of at most n_peers (V, VB) pairs.

  Returns (True, None) if the instance is empty.
  Returns (True, v) if the instance is reserved.
  Returns (False, None) if a quorum of acceptors failed to reply.
  """
  if not asyncrpc._is_majority(n_peers, values):
    return (False, None)

  empty = True
  maxVB = None
  maxV = None
  for (V, VB) in values:
    if VB is not None and (empty or VB > maxVB):
      maxV = V
      maxVB = VB
      empty = False

  if empty:
    return (True, None)

  return (True, maxV)


class _acceptor_rpc:
  def __init__(self, q):
    self._queue = q

  def prepare(self, return_, i, b):
    self._queue.put((return_, "prepare", (i, b)))

  def accept(self, return_, i, b, v):
    self._queue.put((return_, "accept!", (i, b, v)))


class _acceptor(threading.Thread):
  """
  Implements a paxos acceptor.
  """

  def __init__(self, zctx, endpoint, client_endpoints, db):
    """
    Initializes this acceptor. We listen for messages from proposers/learners
    on 'endpoint' and send replies to clients who identify themself with
    endpoints in 'client_endpoints'. This is not a security mechanism.
    """
    threading.Thread.__init__(self)
    self._queue = queue.Queue()
    self._rpc = asyncrpc.Server(zctx, endpoint, _acceptor_rpc(self._queue))
    self._clients = client_endpoints
    self._db = db

    self.daemon = True

  def run(self):
    for client in self._clients:
      self._rpc.add_client(client)
    self._rpc.start()

    while True:
      return_, message, args = self._queue.get()

      if message == "prepare":
        # Phase 1:
        i, b = args
        ikey = "acceptor." + str(i)
        B, V, VB = self._db.get(ikey) or (None, None, None)
        if B is None or B <= b:
          # Grant the request
          B = b
          self._db.put(ikey, (B, V, VB))
          return_(("promise", i, b, V, VB))
        else:
          # Proposer's B is less than the value we already promised; ignore.
          pass

      elif message == "accept!":
        # Phase 2:
        i, b, v = args
        ikey = "acceptor." + str(i)
        B, V, VB = self._db.get(ikey) or (None, None, None)
        if B is None or B <= b:
          # Grant the request
          B = b
          V = v
          VB = b
          self._db.put(ikey, (B, V, VB))
          return_(("learn", i, b, v))
        else:
          # Proposer's B is less than the value we already promised; ignore.
          pass


class _learner(threading.Thread):
  """
  Implements a paxos learner.
  """

  def __init__(self, zctx, endpoint, peers, timeout):
    threading.Thread.__init__(self)
    self._peers = peers
    self._queue = queue.Queue()
    self._rpcclient = asyncrpc.MultiClient(zctx, endpoint)
    for peer in peers:
      self._rpcclient.add_server(peer)
    self._rpcclient.set_timeout(timeout)
    self._values = {}
    self._maxi = None

  def learn(self, i, val):
    # Acceptor tells us this value has been chosen for this round.
    self._values[i] = val

    # TODO resolve holes elsewhere and don't block acceptor thread.

    if self._maxi is None or self._maxi < i:
      self._maxi = i

  def value(self, i):
    # TODO don't deliver i if i-1 hasn't been delivered yet or resolve holes or
    # something.
    if i in self._values:
      return ("KNOW", self._values[i])

    return ("DONT_KNOW",)

  def run(self):
    while True:
      # TODO periodically emit state of highest instance for which some value was
      # accepted from acceptor -> learner. (Have learner be a thread; query
      # acceptors at some interval.)
      time.sleep(5)


class _proposer(threading.Thread):
  """
  Implements a paxos proposer.
  """

  def __init__(self, zctx, endpoint, peers, timeout, peerid, learner):
    threading.Thread.__init__(self)
    self._peers = peers
    self._queue = queue.Queue()
    self._rpcclient = asyncrpc.MultiClient(zctx, endpoint)
    for peer in peers:
      self._rpcclient.add_server(peer)
    self._timeout = timeout
    self._peerid = peerid
    self._learner = learner

    self.daemon = True

  def nextballot(self, b):
    """
    Generate distinct ballot number (for this proposer) greater than 'b'.
    """
    N = len(self._peers)
    i = self._peerid - (b % N)
    if i <= 0:
      i += N
    return b + i

  def propose(self, value):
    self._queue.put(value)

  def run(self):
    i = 1  # TODO pick i more intelligently?
    b = self.nextballot(0)  # TODO same?
    v = None
    self._rpcclient.set_timeout(self._timeout)

    begin, retryphase1 = 1, 2
    state = begin

    while True:
      if state == begin:
        v = self._queue.get()
      elif state == retryphase1:
        state = begin

      # Phase 1:
      resps = self._rpcclient.prepare(i, b)

      # We can only send our 'v' for acceptance if we have not already crossed
      # the Rubicon: if any other v *possibly* has quorum, we can't submit.
      # Each resp in resps is a ("promise", i, b, V, VB).
      maj, res_val = _majority(len(self._peers), [resp[3:5] for resp in resps])

      if not maj:
        state = retryphase1
        b = self.nextballot(b)
        continue
      
      # Instance is ready, proceed. Phase 2:
      if res_val is not None:
        v = res_val  # Instance is reserved; we must choose this value.

      resps = self._rpcclient.accept(i, b, v)
      if not asyncrpc._is_majority(len(self._peers), resps):
        state = retryphase1
        b = self.nextballot(b)
        continue

      # Instance is closed. Convey "learn" messages to local learner.
      self._learner.learn(i, v)
      i += 1


class agent:
  """
  Implements a paxos agent (acceptor, proposer, learner). At present performs
  the basic (i.e., single value) consensus protocol.
  """

  def __init__(self, zctx, db, timeout, learner_endpoint, proposer_endpoint, \
      acceptor_endpoint, all_client_endpoints, all_acceptor_endpoints, peerid):
    """
    Initializes a paxos agent with this ZMQ context, database object, timeout,
    and various ZMQ addresses, as well as a unique peer id.

    Timeout is in seconds (int, long, or float types are ok).

    Peer id must be unique for this paxos group and in the range [0, n_peers].

    The database object implements the following API and semantics:

      db.get("string_key"):
        Look up the value associated with the given key.
        Returns None if no such key exists; otherwise returns the value.

      db.put("string_key", python_value):
        Atomically and durably stores the given python value at the given key.
        (At this time, your database must be able to serialize arbitrary python
        objects. In practice we're only going to be storing integers and user-
        provided values. In the future we may limit user-provided values to
        strings.)
    """
    self._acceptor = \
        _acceptor(zctx, acceptor_endpoint, all_client_endpoints, db)
    self._learner = \
        _learner(zctx, learner_endpoint, all_acceptor_endpoints, timeout)
    self._proposer = \
        _proposer(zctx, proposer_endpoint, all_acceptor_endpoints, timeout, \
        peerid, self._learner)

    self._acceptor.start()
    self._proposer.start()
    self._learner.start()

  def propose(self, value):
    self._proposer.propose(value)

  def value(self, i):
    return self._learner.value(i)
