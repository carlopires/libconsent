// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#ifndef SRC_LL_AGENT_H_
#define SRC_LL_AGENT_H_

#include <tr1/memory>

#include <zmq.hpp>

#include "../include/libconsentpp.h"

using std::tr1::shared_ptr;

namespace LibConsent {
namespace LowLevel {

class Agent : AgentInterface {
 public:
  Agent();
  virtual void set_log_callback(LogCallback callback);
  virtual void set_storage_callbacks(StoragePut putter, StorageGet getter);
  virtual void AddPeers(const char *zmq_str, int num_peers);
  virtual void RemovePeers(const char *zmq_str, int num_peers);
  virtual void SetUniquePeerNumber(int n);
  virtual void AddBind(const char *zmq_str);
  virtual void RemoveBind(const char *zmq_str);
  virtual void Start(bool recover);
  virtual void Submit(const char *value, int value_len);

 private:
  LogCallback log_callback_;
  StoragePut storage_put_;
  StorageGet storage_get_;

  shared_ptr<zmq::context_t> zmq_;

  DISALLOW_COPY_AND_ASSIGN(Agent);
};

}  // namespace LowLevel
}  // namespace LibConsent

#endif  // SRC_LL_AGENT_H_
