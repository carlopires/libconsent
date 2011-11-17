# Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
#
# This work is placed under the MIT license, the full text of which is
# included in the `COPYING' file at the root of the project sources.
#
# Author(s): Conrad Meyer

import queue
import threading
import zmq

from libconsent import asyncrpc

# Takes in a number of peers, and a list of at most n_peers values.
# Returns (True, v) if any value v has quorum.
# Returns (False, None) if no value has quorum.
def _majority(n_peers, values):
  if len(values) < ((n_peers // 2) + 1):
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


class _acceptor_rpc:
  def __init__(self, q):
    self._queue = q

  def prepare(self, return_, N):
    self._queue.put((return_, "prepare", N))

  def accept(self, return_, N, v):
    self._queue.put((return_, "accept!", (N, v)))

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
        propose_N = args
        if self._db.get("N") is None or propose_N > self._db.get("N"):
          self._db.put("N", propose_N)
          return_(("promise", propose_N, self._db.get("V")))
        else:
          # Proposer's N is less than the value we already promised; ignore.
          pass

      elif message == "accept!":
        # Phase 2:
        propose_N, propose_v = args
        if self._db.get("N") is None or self._db.get("N") <= propose_N:
          self._db.put("N", propose_N)
          self._db.put("V", propose_v)

        # Proposers don't really need to know if we accepted their proposal
        # or not.
        #return_(None)

      elif message == "query":
        # Dump any state we have if a learner asks.
        return_((self._db.get("N"), self._db.get("V")))


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

  def value(self):
    # Just ask acceptors what they think they've decided on.
    resps = self._rpcclient.query()
    maj, maj_val = _majority(len(self._peers), [resp[1] for resp in resps])

    # If a quorum agree on a value (and, implementation detail, that value
    # isn't None), return it.
    if maj and maj_val is not None:
      return ("KNOW", maj_val)
    else:
      return ("DONT_KNOW",)


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

    self.daemon = True

  def propose(self, value):
    self._queue.put(value)

  def run(self):
    N = 0
    while True:
      # Really basic state machine. Do a proposal round for every value given
      # to us.
      v = self._queue.get()

      # Phase 1:
      self._rpcclient.set_timeout(self._timeout)
      resps = self._rpcclient.prepare(N)

      # We can only send our 'v' for acceptance if we have not already crossed
      # the Rubicon: if any other v *possibly* has quorum, we can't submit.
      maj, maj_val = _majority(len(self._peers), [resp[2] for resp in resps])

      if maj:  # We need quorum promises to submit one way or the other.
        # Phase 2:

        if maj_val is not None:
          v = maj_val

        self._rpcclient.set_timeout(0)  # accept! doesn't trigger a reply.
        self._rpcclient.accept(N, v)

      N += 1



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
