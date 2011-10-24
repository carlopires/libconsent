// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#include "./learner.h"

namespace LibConsent {

int Learner::Init(Agent *agent, zmqmm::context_t *zmq, Acceptor *acceptor,
    LogCallback cb) {
  // TODO(Conrad) bring up sockets; verify that connect() succeeds on each
  // endpoint.
  return -1;
}

void Learner::Start() {
}

}  // namespace LibConsent
