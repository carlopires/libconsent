# Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
#
# This work is placed under the MIT license, the full text of which is
# included in the `COPYING' file at the root of the project sources.
#
# Author(s): Conrad Meyer

import zmq

class pair:
  """
  psuedopair.pair is an object that looks kind of like a zmq.PAIR socket
  (e.g., bidirectional communication) with a few differences.

  1) Message delivery is (intentionally) unreliable.
  2) It can be used with any ZMQ endpoints, not just inproc.
  2) psuedopair.pair requires you to both bind() and connect() (with separate
     endpoints).
  3) It can't be passed directly to a Poller, so it provides register() and
     unregister() methods which add/remove itself to/from a Poller.
  """

  def __init__(self, zmq_context):
    """
    Creates a psuedopair.pair associated with the given zmq context.
    """
    self._sub = zmq_context.socket(zmq.SUB)
    self._sub.setsockopt(zmq.SUBSCRIBE, b'')
    self._pub = zmq_context.socket(zmq.PUB)

    self._pub_endpoints = set()
    self._sub_endpoints = set()

  def bind(self, endpoint):
    """
    Binds this pair to listen on the given endpoint.
    """
    self._sub.bind(endpoint)
    self._sub_endpoints.add(endpoint)

  def connect(self, endpoint):
    """
    Connect this socket to broadcast to the given endpoint.
    """
    self._pub.connect(endpoint)
    self._pub_endpoints.add(endpoint)

  def send_pyobj(self, pyobj, flags=0):
    """
    Sends the given python object. 'flags' is the same as for regular PyZMQ
    socket send*() methods.
    """
    if len(self._sub_endpoints) == 0 or len(self._pub_endpoints) == 0:
      raise ValueError("psuedopair needs to be bound _and_ connected")
    self._pub.send_pyobj(pyobj, flags)

  def recv_pyobj(self, flags=0):
    """
    Receives a python object. 'flags' is the same as for regular PyZMQ socket
    recv*() methods.
    """
    if len(self._sub_endpoints) == 0 or len(self._pub_endpoints) == 0:
      raise ValueError("psuedopair needs to be bound _and_ connected")
    return self._sub.recv_pyobj(flags)

  def register(self, poller, flags=zmq.POLLIN|zmq.POLLOUT):
    """
    Registers this psuedopair.pair with the given PyZMQ Poller. 'flags' is the
    same as for PyZMQ Poller's register() method.
    """
    if zmq.POLLIN & flags:
      poller.register(self._sub, zmq.POLLIN)
    if zmq.POLLOUT & flags:
      poller.register(self._pub, zmq.POLLOUT)

  def unregister(self, poller):
    """
    Unregisters this pair from the given PyZMQ Poller.
    """
    # dirty hack here:
    if self._sub in poller.__dict__['sockets']:
      poller.unregister(self._sub)
    if self._pub in poller.__dict__['sockets']:
      poller.unregister(self._pub)

  def endpoints(self):
    """
    Returns a pair (recv_endpoints, send_endpoints), where recv_endpoints is a
    python set() of bound (listening) endpoints, and send_endpoints is a python
    set() of connected (broadcasting) endpoints.
    """
    return (self._sub_endpoints, self._pub_endpoints)
