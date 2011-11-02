// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#include "./acceptor.h"
#include "./agent.h"
#include "./util.h"

namespace LibConsent {

std::string Acceptor::output_endpoint() {
  return output_endpoint_;
}

int Acceptor::Init(Agent *agent, zmqmm::context_t *zmq) {
  int peer_num = agent->unique_peer_number();

  output_endpoint_ += "inproc://acceptor-";
  output_endpoint_ += peer_num;
  output_endpoint_ += "output";

  std::set<std::string> multicasts = agent->multicast_endpoints();

  if (input_socket_.init(zmq, ZMQ_SUB) == -1) return -1;
  for (auto it = multicasts.begin(); it != multicasts.end(); ++it)
    if (input_socket_.bind(it->c_str()) == -1) return -1;
  if (input_socket_.setsockopt(ZMQ_SUBSCRIBE, NULL, 0) == -1) return -1;

  if (output_socket_.init(zmq, ZMQ_PUB) == -1) return -1;
  if (output_socket_.bind(output_endpoint_.c_str()) == -1) return -1;

  for (int i = 0; i < agent->num_peers(); i++) {
    if (proposer_sockets_[i].init(zmq, ZMQ_PUB) == -1) return -1;
    if (proposer_sockets_[i].connect(agent->peer_endpoint(i)) == -1)
      return -1;
  }

  return 0;
}

void *AcceptorRun(void *acceptor_) {
  // Acceptor *acceptor = reinterpret_cast<Acceptor *>(acceptor_);
  // TODO(Conrad): Follow state machine for Acceptor.
  return NULL;
}

void Acceptor::Start() {
  pthread_t thread_id;
  int s = pthread_create(&thread_id, NULL, AcceptorRun,
      reinterpret_cast<void *>(this));
  LC_ASSERT(s == 0);
}

}  // namespace LibConsent
