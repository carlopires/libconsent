// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#include "./acceptor.h"

namespace LibConsent {

double Acceptor::get_timeout_percent() {
  return 0.0;
}

int Acceptor::Init(Agent *agent, zmqmm::context_t *zmq) {
  // TODO(Conrad) bring up sockets; verify that connect() succeeds on each
  // endpoint.
  return -1;
}

void Acceptor::Start() {
}

}  // namespace LibConsent
