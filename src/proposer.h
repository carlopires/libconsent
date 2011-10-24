// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#ifndef SRC_PROPOSER_H_
#define SRC_PROPOSER_H_

#include <string>

#include "../include/libconsentpp.h"
#include "./zmqmm.h"

namespace LibConsent {

class Agent;

class Proposer {
 public:
  Proposer() { messages_expected_ = messages_received_ = 0; }

  // Returns a calculation of the fraction of replies we expected to get,
  // but did not, against the number of requests sent.
  double get_timeout_percent();

  // Returns the ZMQ endpoint a client should submit new log values to.
  // Protocol is simply a series of single-part messages; the message length
  // and contents determine the log value.
  std::string input_endpoint();

  // Initialize this Proposer; returns -1 on error, setting errno (potentially
  // a ZMQ errno, however; use zmq_strerror(3).
  int Init(Agent *agent, zmqmm::context_t *zmq);

  // Starts this Proposer running in its own thread.
  void Start();

 private:
  int64_t messages_expected_, messages_received_;
  DISALLOW_COPY_AND_ASSIGN(Proposer);
};

}  // namespace LibConsent

#endif  // SRC_PROPOSER_H_
