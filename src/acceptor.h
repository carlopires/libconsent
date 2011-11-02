// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#ifndef SRC_ACCEPTOR_H_
#define SRC_ACCEPTOR_H_

#include <string>
#include <vector>

#include "../include/libconsentpp.h"
#include "./zmqmm.h"

namespace LibConsent {

class Agent;

class Acceptor {
 public:
  Acceptor() {}

  // The endpoint to subscribe to to get learner messages. The protocol is a
  // series of two-part messages; the first part is a protocol buffers
  // header and the second part is the log "value".
  std::string output_endpoint();

  // Initialize this Acceptor; returns -1 on error, setting errno (potentially
  // a ZMQ errno, however; use zmq_strerror(3).
  int Init(Agent *agent, zmqmm::context_t *zmq);

  // Starts this Acceptor running in its own thread.
  void Start();

 private:
  zmqmm::socket_t input_socket_, output_socket_;
  std::vector<zmqmm::socket_t> proposer_sockets_;
  std::string output_endpoint_;

  DISALLOW_COPY_AND_ASSIGN(Acceptor);
};

}  // namespace LibConsent

#endif  // SRC_ACCEPTOR_H_
