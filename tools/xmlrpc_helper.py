import sys
import xmlrpc.client

# python3 xmlrpc_helper.py http://host:port method [arg1 [arg2 [...]]]

server = xmlrpc.client.ServerProxy(sys.argv[1])
print(getattr(server, sys.argv[2])(*sys.argv[3:]))
