# Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
#
# This work is placed under the MIT license, the full text of which is
# included in the `COPYING' file at the root of the project sources.
#
# Author(s): Conrad Meyer
#
# Runs a bunch of paxos instances locally using a trivial DB.

import sys
import time
import zmq

import libconsent.asyncrpc as asyncrpc
import libconsent.paxos as paxos
import libconsent.test.tdb as tdb

TCP = 0x15
IPC = 0x16
INPROC = 0x17

def _uniq_port_gen():
  port = 8899
  while True:
    yield port
    port += 1

_uniq_port = _uniq_port_gen().__next__

def _gen_tcp_ep(an, et):
    return "tcp://127.0.0.1:" + str(_uniq_port())

def _gen_ipc_ep(an, et):
  return "ipc:///tmp/paxos-%s-%s" % (an, et)

def _gen_inproc_ep(an, et):
  return "inproc://paxos-%s-%s" % (an, et)

_gen_ep = { TCP: _gen_tcp_ep, IPC: _gen_ipc_ep, INPROC: _gen_inproc_ep }

asyncrpc.DEBUG_LOG = True
asyncrpc.DEBUG_TIMING = 0.05


class _Runner:
  def __init__(self, mtype, agent_names, timeout):
    self.zctx = zmq.Context()

    acc_ep = {}
    learn_ep = {}
    prop_ep = {}
    for agent_name in agent_names:
      acc_ep[agent_name] = _gen_ep[mtype](agent_name, 'a')
      learn_ep[agent_name] = _gen_ep[mtype](agent_name, 'l')
      prop_ep[agent_name] = _gen_ep[mtype](agent_name, 'p')

    all_acc_eps = list(acc_ep.values())
    all_client_eps = list(learn_ep.values()) + list(prop_ep.values())

    dbs = {}
    agents = {}
    uniq_peer_no = 0
    for agent_name in agent_names:
      db = tdb.open(agent_name + ".db")
      dbs[agent_name] = db
      agents[agent_name] = paxos.agent(self.zctx, db, timeout, \
          learn_ep[agent_name], prop_ep[agent_name], acc_ep[agent_name], \
          all_client_eps, all_acc_eps, uniq_peer_no)

      uniq_peer_no += 1

    self.dbs = dbs
    self.agents = agents
    for (an, ag) in agents.items():
      setattr(self, an, ag)


def new(mtype, agent_names, timeout=0.1):
  """
  Initialize several local instances of libconsent paxos agents. `mtype'
  corresponds to one of TCP, IPC, or INPROC; `agent_names' is a list of
  names for these agents.
  """

  return _Runner(mtype, agent_names, timeout)
