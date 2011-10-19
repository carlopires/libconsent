// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#ifndef SRC_LL_AGENT_H_
#define SRC_LL_AGENT_H_

#include <tr1/memory>

#include "../include/libconsentpp.h"
#include "./zmqmm.h"

using std::tr1::shared_ptr;

namespace LibConsent {
namespace LowLevel {

class Agent : public AgentInterface {
 public:
  Agent();
  virtual void set_log_callback(LogCallback callback);
  virtual void set_storage_callbacks(StoragePut putter, StorageGet getter);
  virtual int unique_peer_number();
  virtual void set_unique_peer_number(int n);
  virtual int message_timeout_interval();
  virtual void set_message_timeout_interval(int t);
  virtual double get_timeout_percent();

  virtual void AddPeers(const char *zmq_str, int num_peers);
  virtual void RemovePeers(const char *zmq_str, int num_peers);
  virtual void AddBind(const char *zmq_str);
  virtual void RemoveBind(const char *zmq_str);
  virtual void Start(bool recover);
  virtual void Submit(const char *value, int value_len);

 private:
  // These variables are run-time mutable and require locking:
  pthread_rwlock_t rwlock_;
  LogCallback log_callback_;
  StoragePut storage_put_;
  StorageGet storage_get_;
  int unique_peer_number_, message_timeout_interval_, num_peers_;
  int64_t stats_messages_expected_, stats_messages_received_;

  // These are constant post-construction:
  shared_ptr<zmqmm::context_t> zmq_;

#ifdef LIBCONSENT_ASSERT_LOG_
  int assert_log_fd_;
#endif

  DISALLOW_COPY_AND_ASSIGN(Agent);
};

}  // namespace LowLevel
}  // namespace LibConsent

#endif  // SRC_LL_AGENT_H_
