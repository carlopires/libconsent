#!/usr/bin/python3 -tt

import sys
import threading
import time
import xmlrpc.client
import xmlrpc.server

class rpcsurface:
  def __init__(self, myrpc, peers):
    self.peers = peers
    self.myrpc = myrpc
    self.lock = threading.Lock()

  def propose(self, value):
    self.lock.acquire()
    # TODO
    self.lock.release()

  def learn(self):
    self.lock.acquire()
    # TODO
    self.lock.release()

  def testing(self):
    self.lock.acquire()
    print("Testing!")
    self.lock.release()

def usage():
  print("Usage:")
  print("  replica.py <filename.db> <myaddr> <peers>")
  print()
  print("filename.db - Local file to use as the durable storage for paxos")
  print("myaddr      - The host, port tuple to use for this node")
  print("peers       - Comma delimited list of host, port tuples for acceptor peers")

def main(args):
  if len(args) < 3:
    usage()
    sys.exit(1)

  db, myaddr, peers = args[:3]
  peers = peers.split(",")
  myaddr = myaddr.rsplit(":", 1)
  myaddr = (myaddr[0], int(myaddr[1]))

  peerrpcs = [xmlrpc.client.ServerProxy("http://" + x) for x in peers]

  myrpc = xmlrpc.server.SimpleXMLRPCServer(myaddr, allow_none=True)
  myrpc.register_instance(rpcsurface(myrpc, peerrpcs))
  myrpc.serve_forever()

if __name__ == "__main__":
  main(sys.argv[1:])
