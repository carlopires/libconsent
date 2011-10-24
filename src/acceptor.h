// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#ifndef SRC_ACCEPTOR_H_
#define SRC_ACCEPTOR_H_

#include "../include/libconsentpp.h"
#include "./zmqmm.h"

namespace LibConsent {

class Agent;

class Acceptor {
 public:
  Acceptor() {}
  double get_timeout_percent();
  int Init(Agent *agent, zmqmm::context_t *zmq);
  void Start();

 private:
  DISALLOW_COPY_AND_ASSIGN(Acceptor);
};

}  // namespace LibConsent

#endif  // SRC_ACCEPTOR_H_
