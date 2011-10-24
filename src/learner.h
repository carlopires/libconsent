// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#ifndef SRC_LEARNER_H_
#define SRC_LEARNER_H_

#include "../include/libconsentpp.h"
#include "./zmqmm.h"

namespace LibConsent {

class Agent;
class Acceptor;

class Learner {
 public:
  Learner() {}

  // Initialize this Learner; returns -1 on error, setting errno (potentially
  // a ZMQ errno, however; use zmq_strerror(3). Learns from the acceptor
  // specified; outputs to `callback'.
  int Init(Agent *agent, zmqmm::context_t *zmq, Acceptor *acceptor,
      LogCallback callback);

  // Starts this Learner running in its own thread.
  void Start();

 private:
  LogCallback callback_;
  zmqmm::socket_t listen_socket_;
  DISALLOW_COPY_AND_ASSIGN(Learner);
};

}  // namespace LibConsent

#endif  // SRC_LEARNER_H_
