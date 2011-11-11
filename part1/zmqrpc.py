# Conrad Meyer <cemeyer@uw.edu>
# 0824410
# CSE 550 Problem Set 3
# Thu Nov 10 2011

import threading
import zmq

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
      req = self.socket.recv_pyobj()
      rep = None

      try:
        rep = self.methods[req[0]](*req[1])

      except Exception as e:
        print(e)
        pass

      self.socket.send_pyobj(rep)

class Client:
  def __init__(self, zctx, endpoint):
    self._socket = zctx.socket(zmq.REQ)
    self._socket.connect(endpoint)

  class _Call:
    def __init__(self, sock, name):
      self.socket = sock
      self.name = name

    def __call__(self, *args):
      self.socket.send_pyobj((self.name, args))
      return self.socket.recv_pyobj()

  def __getattr__(self, name):
    return Client._Call(self._socket, name)
