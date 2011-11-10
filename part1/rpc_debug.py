#!/usr/bin/python3 -tt

import sys
import xmlrpc.client

server = xmlrpc.client.ServerProxy(sys.argv[1])
getattr(server, sys.argv[2])(*sys.argv[3:])
