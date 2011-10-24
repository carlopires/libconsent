// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#ifndef SRC_PROPOSER_H_
#define SRC_PROPOSER_H_

#include <set>
#include <string>
#include <vector>

#include "../include/libconsentpp.h"
#include "./zmqmm.h"

namespace LibConsent {

class Agent;

class Proposer {
 public:
  Proposer();
  const char *input_endpoint();
  // TODO(Conrad) bring up sockets; verify that connect() succeeds on each
  // endpoint.
  int Init(Agent *agent, zmqmm::context_t *zmq);
  void Start();

 private:
  DISALLOW_COPY_AND_ASSIGN(Proposer);
};

}  // namespace LibConsent

#endif  // SRC_PROPOSER_H_
