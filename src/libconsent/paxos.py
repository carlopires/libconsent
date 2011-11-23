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

# TODO periodically emit state of highest instance for which some value was
# accepted from acceptor -> learner.
# TODO wait for quorum replies in asyncrpc instead of all.

import queue
import threading
import zmq

from libconsent import asyncrpc

def _is_majority(n_peers, values):
  if len(values) < ((n_peers // 2) + 1):
    return False
  return True

# Takes in a number of peers, and a list of at most n_peers (V, VB) pairs.
# Returns (True, None) if the instance is empty.
# Returns (True, v) if the instance is reserved.
# Returns (False, None) if a quorum of acceptors failed to reply.
# TODO {
def _majority(n_peers, values):
  if not _is_majority(n_peers, values):
    return (False, None)

  # Count the number of occurrences of each value.
  v_counts = []
  for v in values:
    found = False
    for rec in v_counts:
      if rec[0] == v:
        rec[1] += 1
        found = True
    if not found:
      v_counts.append([v, 1])

  # If any value has quorum, return it.
  for (v, count) in v_counts:
    if count >= ((n_peers // 2) + 1):
      return (True, v)

  return (False, None)
# }


class _acceptor_rpc:
  def __init__(self, q):
    self._queue = q

  def prepare(self, return_, i, b):
    self._queue.put((return_, "prepare", (i, b)))

  def accept(self, return_, i, b, v):
    self._queue.put((return_, "accept!", (i, b, v)))

  def query(self, return_):
    self._queue.put((return_, "query", None))


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
        ikey = "acceptor." + i
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
        ikey = "acceptor." + i
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

      # TODO {
      elif message == "query":
        # Dump any state we have if a learner asks.
        return_((self._db.get("N"), self._db.get("V")))
      # }


class _learner:
  """
  Implements a paxos learner.
  """

  def __init__(self, zctx, endpoint, peers, timeout):
    self._peers = peers
    self._queue = queue.Queue()
    self._rpcclient = asyncrpc.MultiClient(zctx, endpoint)
    for peer in peers:
      self._rpcclient.add_server(peer)
    self._rpcclient.set_timeout(timeout)

  def learn(self, i, val):
    # TODO

  def value(self):
    # TODO {
    # Just ask acceptors what they think they've decided on.
    resps = self._rpcclient.query()
    maj, maj_val = _majority(len(self._peers), [resp[1] for resp in resps])

    # If a quorum agree on a value (and, implementation detail, that value
    # isn't None), return it.
    if maj and maj_val is not None:
      return ("KNOW", maj_val)
    else:
      return ("DONT_KNOW",)
    # }


class _proposer(threading.Thread):
  """
  Implements a paxos proposer.
  """

  def __init__(self, zctx, endpoint, peers, timeout):
    threading.Thread.__init__(self)
    self._peers = peers
    self._queue = queue.Queue()
    self._rpcclient = asyncrpc.MultiClient(zctx, endpoint)
    for peer in peers:
      self._rpcclient.add_server(peer)
    self._timeout = timeout
    # TODO {
    self._peerid = XXX # must be unique number
    self._learner = XXX
    # }

    self.daemon = True

  def nextballot(self, b):
    # TODO : Must generate distinct ballot number (for this proposer) greater
    # than 'b'.
    pass

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
      if not _is_majority(len(self._peers), resps):
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
      acceptor_endpoint, all_client_endpoints, all_acceptor_endpoints):
    """
    Initializes a paxos agent with this ZMQ context, database object, timeout,
    and various ZMQ addresses.

    Timeout is in seconds (int, long, or float types are ok).

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
    self._proposer = \
        _proposer(zctx, proposer_endpoint, all_acceptor_endpoints, timeout)
    self._learner = \
        _learner(zctx, learner_endpoint, all_acceptor_endpoints, timeout)

    self._acceptor.start()
    self._proposer.start()

  def propose(self, value):
    self._proposer.propose(value)

  def value(self):
    return self._learner.value()
