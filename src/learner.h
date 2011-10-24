// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#ifndef SRC_LEARNER_H_
#define SRC_LEARNER_H_

#include <set>
#include <string>
#include <vector>

#include "../include/libconsentpp.h"
#include "./zmqmm.h"

namespace LibConsent {

class Agent;
class Acceptor;

class Learner {
 public:
  Learner();
  // TODO(Conrad) bring up sockets; verify that connect() succeeds on each
  // endpoint.
  int Init(Agent *agent, zmqmm::context_t *zmq, Acceptor *acceptor,
      LogCallback cb);
  void Start();

 private:
  DISALLOW_COPY_AND_ASSIGN(Learner);
};

}  // namespace LibConsent

#endif  // SRC_LEARNER_H_
