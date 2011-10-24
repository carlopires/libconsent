// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#ifndef SRC_AGENT_H_
#define SRC_AGENT_H_

#include <set>
#include <string>
#include <vector>

#include "../include/libconsentpp.h"
#include "./zmqmm.h"

#include "./acceptor.h"
#include "./learner.h"
#include "./proposer.h"

namespace LibConsent {

class Agent : public AgentInterface {
 public:
  Agent();
  virtual void set_log_callback(LogCallback callback);
  virtual void set_storage_callbacks(StoragePut putter, StorageGet getter);
  virtual int message_timeout_interval();
  virtual void set_message_timeout_interval(int t);
  virtual double get_timeout_percent();
  virtual void set_num_peers(int n);
  virtual int num_peers();
  virtual int unique_peer_number();
  virtual void set_unique_peer_number(int n);
  virtual void set_peer_endpoint(int peer_number, const char *zmq_endpoint);
  virtual const char *peer_endpoint(int peer_number);
  virtual void add_multicast_endpoint(const char *zmq_endpoint);
  virtual void remove_multicast_endpoint(const char *zmq_endpoint);

  virtual void Start();
  virtual void Submit(const char *value, int value_len);

 private:
  // Configuration:
  LogCallback log_callback_;
  StoragePut storage_put_;
  StorageGet storage_get_;
  int unique_peer_number_, message_timeout_interval_, num_peers_;
  std::vector<std::string> peer_endpoints_;
  std::set<std::string> multicast_endpoints_;

  // Run-time objects:
  zmqmm::context_t zmq_;
  Acceptor acceptor_;
  Proposer proposer_;
  Learner learner_;

#ifdef LIBCONSENT_ASSERT_LOG_
  int assert_log_fd_;
#endif

  DISALLOW_COPY_AND_ASSIGN(Agent);
};

}  // namespace LibConsent

#endif  // SRC_AGENT_H_
