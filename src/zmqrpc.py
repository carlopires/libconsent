# Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
#
# This work is placed under the MIT license, the full text of which is
# included in the `COPYING' file at the root of the project sources.
#
# Author(s): Conrad Meyer

import threading
import time
import zmq

# Turns an arbitrary python object into an RPC server by introspecting and
# ignoring private (i.e., "_"-prefixed) methods.
class Server(threading.Thread):
  def __init__(self, zctx, endpoint, obj):
    threading.Thread.__init__(self)
    self.methods = {}
    for x in dir(obj):
      if not x.startswith("_"):
        self.methods[x] = getattr(obj, x)
    self.socket = zctx.socket(zmq.REP)
    self.socket.bind(endpoint)
    self.daemon = True
    self.start()

  def run(self):
    while True:
      # Deserialize,
      req = self.socket.recv_pyobj()
      rep = None

      try:
        # Call,
        rep = self.methods[req[0]](*req[1])

      except Exception as e:
        print(e)
        pass

      # And serialize the response.
      self.socket.send_pyobj(rep)


# Clients are fairly dumb; they'll just serialize calls into them and send
# the bits on to the server end of things (de-serializing responses, of
# course).
class Client:
  def __init__(self, zctx, endpoint):
    self._socket = zctx.socket(zmq.REQ)
    self._socket.connect(endpoint)
    self._needs_recv = False

  # We attempt to cleverly handle asynchronously available servers by
  # dropping backed-up requests to them, and occasionally checking to see
  # if they've come back. Obviously this doesn't work if the server totally
  # crashes because it'll never reply to a request it hasn't gotten; the
  # solution to this is to use PUB/SUB and message passing instead of REQ/REP.
  # 20-20 hindsight, motherfucker.
  def _unblock(self):
    try:
      self._socket.recv(zmq.NOBLOCK)
    except zmq.ZMQError as e:
      if e.errno == zmq.EAGAIN:
        return False
      raise
    return True

  # Wrap send/recv in order to do the clever things we talked about ten lines
  # previous.
  def send_pyobj(self, obj):
    if self._needs_recv:
      if self._unblock():
        self._needs_recv = False

    if not self._needs_recv:
      self._socket.send_pyobj(obj)
      self._needs_recv = True

  def recv_pyobj(self):
    o = self._socket.recv_pyobj()
    self._needs_recv = False
    return o

  # Syntax sugar.
  class _Call:
    def __init__(self, name, client):
      self.name = name
      self.client = client

    def __call__(self, *args):
      self.client.send_pyobj((self.name, args))
      return self.client.recv_pyobj()

  def __getattr__(self, name):
    return Client._Call(name, self)

  # A basic Future so that we can send out many RPCs simultaneously and check
  # for responses modulo some timeout.
  class _FutureCall:
    def __init__(self, name, client, args):
      self.client = client
      self.client.send_pyobj((name, args))

    def socket(self):
      return self.client._socket

    def force(self):
      return self.client.recv_pyobj()

  def async_call(self, name, args):
    return Client._FutureCall(name, self, args)

# Performs a given RPC against a set of peers; returns when a quorum of servers has
# replied, after the timeout interval (in seconds) has passed, whichever happens
# first. (Actually, returns when *all* servers has replied, or the timeout has
# occurred. Waiting for quorum just seems stupid esp. with our RPC REQ/REP socket
# interface.)
#
# On success, returns (True, values), where values is a list of at least quorum
#   values.
# On timeout, returns (False, values).
def async_multicall(peers, timeout, name, args):
  futures = {}
  for peer in peers:
    future = peer.async_call(name, args)
    futures[future.socket()] = future

  starttime = time.time()
  results = []

  poller = zmq.Poller()
  for future_sock in futures.keys():
    poller.register(future_sock, zmq.POLLIN)

  # while len(results) < ((len(peers) // 2) + 1):  # quit on majority responded
  while len(results) < len(peers):  # quit when everyone responds
    elapsed = time.time() - starttime
    if elapsed >= timeout: break

    for (sock, status) in poller.poll(1000*(timeout - elapsed)):
      if status == zmq.POLLIN:
        poller.unregister(sock)
        results.append(futures[sock].force())

  return (len(results) >= ((len(peers) // 2) + 1), results)
