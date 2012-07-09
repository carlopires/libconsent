# Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
#
# This work is placed under the MIT license, the full text of which is
# included in the `COPYING' file at the root of the project sources.
#
# Author(s): Conrad Meyer

import sys

#if sys.version_info.major < 3:
#	raise Exception("Please use Python 3")

import libconsent.test.localrunner as paxosrunner

runner = None
mode = "TCP"
peer = 'alice'
names = ['alice', 'bob', 'cathy']

def new_runner(names):
	global runner
	runner = paxosrunner.new(getattr(paxosrunner, mode), names, 5)

def usage():
	print("set peer <peername>          - Call against this peer")
	print("set mode <TCP|IPC|INPROC>    - Specify comm. protocol")
	print("set names <name1> ...        - Set agent names")
	print("start                        - Start paxos agents")
	print("propose <val.>               - Propose a value")
	print("value <inst.>                - Observe a value")
	print("exit|quit                    - Quit")

def repl():
	global names
	global peer
	global mode
	global runner

	usage()
	while True:
		sys.stdout.write("> ")
		sys.stdout.flush()
		line = sys.stdin.readline()
		if line == '': return
		line = line.strip().split(" ")

		if line[0] == 'set':
			if line[1] == 'mode':
				mode = line[2]
			elif line[1] == 'peer':
				peer = line[2]
			elif line[1] == 'names':
				names = line[2:]
		elif line[0] == 'start':
			new_runner(names)
		elif line[0] == 'propose':
			getattr(runner, peer).propose(line[1])
		elif line[0] == 'value':
			print(getattr(runner, peer).value(int(line[1])))
		elif line[0] == 'exit' or line[0] == 'quit':
			return
		else:
			usage()

repl()
