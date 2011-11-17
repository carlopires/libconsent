# Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
#
# This work is placed under the MIT license, the full text of which is
# included in the `COPYING' file at the root of the project sources.
#
# Author(s): Conrad Meyer
#
# asyncrpc wire protocol (subject to change):
#   Method calls are a pickled python tuple:
#     (caller_endpoint, nonce, method, args)
#   Return values are also pickled python tuples:
#     (nonce, value)

import random
import threading
import time
import zmq

# If DEBUG_LOG is true, outputs to stdout on every message transmitted /
# received. If DEBUG_TIMING is an numeric value, delays message receipt and
# transmission by a random (uniform distribution) number of seconds between
# zero and the given value.
DEBUG_LOG = False
DEBUG_TIMING = None

def _debug_delay():
  time.sleep(random.uniform(0, DEBUG_TIMING))


class Server(threading.Thread):
  """
  asyncrpc.Server implements an RPC server from a (mostly) arbitrary python
  object's methods (with introspection).
  """

  def __init__(self, zctx, endpoint, rpcobj):
    """
    Initializes this Server with the given ZMQ context, ZMQ endpoint, and
    RPC object.

    Will attempt to call any attribute on rpcobj that doesn't start with '_'.
    RPC object methods must take an object "return_" as their first parameter,
    which can be called to return a value to clients. (If the object is never
    called, nothing is returned to clients.)

    Keeps an explicit list of connected clients, and only responds to these.
    """
    threading.Thread.__init__(self)
    self._methods = {}
    for x in dir(rpcobj):
      if not x.startswith("_"):
        self._methods[x] = getattr(rpcobj, x)
    self._zmq = zctx
    self._sub = zctx.socket(zmq.SUB)
    self._sub.setsockopt(zmq.SUBSCRIBE, b'')
    self._sub.bind(endpoint)
    self._lock = threading.Lock()
    self._clients = {}
    self._client_returns = {}
    self.daemon = True

  def is_client(self, endpoint):
    """
    Is this endpoint currently registered as a client?
    """
    with self._lock:
      return endpoint in self._clients

  class _Return:
    def __init__(self, sock):
      self._socket = sock
      self._lock = threading.Lock()

    def __call__(self, nonce, arg):
      with self._lock:
        if DEBUG_TIMING is not None:
          _debug_delay()
        if DEBUG_LOG:
          print("SERVER XMIT:", nonce, arg)
        self._socket.send_pyobj((nonce, arg))

  def add_client(self, endpoint):
    """
    Add the given endpoint as a client.
    """
    with self._lock:
      sock = self._zmq.socket(zmq.PUB)
      sock.connect(endpoint)
      return_ = Server._Return(sock)
      self._clients[endpoint] = sock
      self._client_returns[endpoint] = return_

  def remove_client(self, endpoint):
    """
    Remove the given endpoint as a client.
    """
    with self._lock:
      del self._clients[endpoint]
      del self._client_returns[endpoint]

  def _client_return(self, endpoint):
    with self._lock:
      return self._client_returns[endpoint]

  def run(self):
    while True:
      try:
        caller, nonce, method, args = self._sub.recv_pyobj()
        if DEBUG_TIMING is not None:
          _debug_delay()
        if DEBUG_LOG:
          print("SERVER RECV:", caller, nonce, method, args)
        if not self.is_client(caller):
          continue

        returner = self._client_return(caller)
        return_ = lambda x: returner(nonce, x)
        self._methods[method](return_, *args)

      except Exception as e:
        print(e)
        pass


class MultiClient:
  """
  asyncrpc.MultiClient implements an asynchronously-available RPC surface
  against multiple asyncrpc.Servers.

  In general, calls to this object send the request to all configured servers;
  If a timeout is configured and not all servers reply before the timeout,
  a list of all responses returned in that time is returned.

  Theoretically, if you can send 4E9 messages fast enough that a server thinks
  it's replying to an RPC 4E9 calls in the past, you might get confusing
  results. Though this seems improbable, users shouldn't assume values returned
  by servers will match the types they expect for the given call. Don't call
  4E9 RPCs with the same MultiClient if this is an issue.
  """

  def __init__(self, zctx, recv_endpoint):
    """
    Initializes this MultiClient with the given ZMQ context and ZMQ endpoint.
    Binds to the endpoint to listen for replies.
    """
    self._zmq = zctx
    self._sub = zctx.socket(zmq.SUB)
    self._sub.setsockopt(zmq.SUBSCRIBE, b'')
    self._sub.bind(recv_endpoint)
    self._sub_endpoint = recv_endpoint
    self._pub = zctx.socket(zmq.PUB)
    self._servers = set()
    self._lock = threading.Lock()
    self._timeout = None
    self._nonce = -2000*1000*1000
    self._poller = zmq.Poller()
    self._poller.register(self._sub, zmq.POLLIN)

  def add_server(self, endpoint):
    """
    Adds a remote server to submit calls against.
    """
    with self._lock:
      self._pub.connect(endpoint)
      self._servers.add(endpoint)

  def remove_server(self, endpoint):
    """
    Removes a configured server.
    """
    with self._lock:
      self._servers.remove(endpoint)
      self._pub = self._zmq.socket(zmq.PUB)
      for endpoint in self._servers:
        self._pub.connect(endpoint)

  def set_timeout(self, timeout):
    """
    Sets the timeout for this MultiClient to use. 'timeout' should be an int or
    double (units of seconds), or None to wait forever.

    N.B.: The client never retries calls, so beware of timeout=None.
    """
    with self._lock:
      self._timeout = timeout

  def __getattr__(self, name):
    # Presents a fake object interface for users to call methods blindly.
    if name.startswith("_"):
      raise AttributeError("uh oh")
    return lambda *args: self._call(name, args)

  def _next_nonce(self):
    # Should only be called by holders of self._lock. Gives the next RPC
    # sequence number.
    res = self._nonce
    self._nonce += 1
    if self._nonce > 2000*1000*1000:
      self._nonce = -2000*1000*1000
    return res

  def _call(self, name, args):
    # Actually performs the call to the remote servers, waits (until timeout,
    # if it is non-None), and returns the results from all servers that
    # responded in time.
    with self._lock:
      nonce = self._next_nonce()
      if DEBUG_TIMING is not None:
        _debug_delay()
      if DEBUG_LOG:
        print("XMIT:", self._sub_endpoint, nonce, name, args)
      self._pub.send_pyobj((self._sub_endpoint, nonce, name, args))

      results = []
      starttime = time.time()

      while len(results) < len(self._servers):
        remaining = None
        if self._timeout is not None:
          elapsed = time.time() - starttime
          if elapsed >= self._timeout: break
          # PyZMQ Poller is in milliseconds:
          remaining = 1000 * (self._timeout - elapsed)

        for (sock, status) in self._poller.poll(remaining):
          try:
            # Pop as many messages off of the socket as we can.
            while True:
              wire_nonce, wire_value = sock.recv_pyobj(zmq.NOBLOCK)
              if nonce == wire_nonce:
                results.append(wire_value)

          # On EAGAIN, we've drained the socket.
          except zmq.ZMQError as e:
            if e.errno != zmq.EAGAIN:
              raise

      if DEBUG_TIMING is not None:
        _debug_delay()
      if DEBUG_LOG:
        print("RECV:", results)
      return results
