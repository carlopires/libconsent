// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#include "./proposer.h"

namespace LibConsent {

double Proposer::get_timeout_percent() {
  return 0.0;
}

std::string Proposer::input_endpoint() {
  return "";
}

int Proposer::Init(Agent *agent, zmqmm::context_t *zmq) {
  // TODO(Conrad) bring up sockets; verify that connect() succeeds on each
  // endpoint.
  return -1;
}

void Proposer::Start() {
}

}  // namespace LibConsent
