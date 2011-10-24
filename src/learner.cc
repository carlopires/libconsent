// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#include "./acceptor.h"
#include "./learner.h"

namespace LibConsent {

int Learner::Init(Agent *agent, zmqmm::context_t *zmq, Acceptor *acceptor,
    LogCallback callback) {
  if (listen_socket_.init(zmq, ZMQ_SUB) == -1) return -1;
  if (listen_socket_.connect(acceptor->output_endpoint().c_str()) == -1)
    return -1;
  if (listen_socket_.setsockopt(ZMQ_SUBSCRIBE, NULL, 0) == -1) return -1;

  callback_ = callback;

  return 0;
}

void Learner::Start() {
}

}  // namespace LibConsent
