# Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
#
# This work is placed under the MIT license, the full text of which is
# included in the `COPYING' file at the root of the project sources.
#
# Author(s): Conrad Meyer

import sys
import time
import xmlrpc.server
import zmq

import libconsent.paxos

# Blah blah boring argument parsing / command-line UX / initialization follows.
def usage():
  print("Usage:")
  print("  replica.py <filename.db> <xmlrpcbind> <accbind> <learnbind> <propbind> \\")
  print("    <clients> <servers>")
  print()
  print("filename.db - Local file to use as the durable storage for paxos")
  print("xmlrpcbind  - TCP endpoint to bind the client interface to ('host:port')")
  print("accbind     - The ZMQ endpoint to use for this node's acceptor")
  print("learnbind   - \"                                       learner")
  print("propbind    - \"                                       proposer")
  print("clients     - Comma delimited list of all ZMQ endpoints for proposers and \\")
  print("              learners in this paxos system")
  print("servers     - \"                                             acceptors in \\")
  print("              this paxos system")

def main(args):
  if len(args) < 7:
    usage()
    sys.exit(1)

  dbfile, xmladdr, accbind, learnbind, propbind, clients, servers = args[:7]
  clients = clients.split(",")
  servers = servers.split(",")

  zctx = zmq.Context()
  agent = libconsent.paxos.agent(zctx, dbfile, learnbind, propbind, accbind, \
      clients, servers)

  xmlrpcserver = xmlrpc.server.SimpleXMLRPCServer(xmladdr.split(":"))
  xmlrpcserver.register_function(lambda x: agent.propose(x), "propose")
  xmlrpcserver.register_function(lambda: agent.learn(), "learn")
  xmlrpcserver.register_introspection_functions()
  xmlrpcserver.serve_forever()

if __name__ == "__main__":
  try:
    main(sys.argv[1:])
  except KeyboardInterrupt:
    print(" Shutting down.")
