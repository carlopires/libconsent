// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#include <cassert>

#include "../include/libconsentpp.h"
#include "./ll_agent.h"

namespace LibConsent {
namespace LowLevel {

Agent::Agent() : zmq_(new zmq::context_t(1)) {
  log_callback_ = NULL;
  storage_put_ = NULL;
  storage_get_ = NULL;
}

void Agent::set_log_callback(LogCallback callback) {
  assert(callback != NULL);
  log_callback_ = callback;
}

void Agent::set_storage_callbacks(StoragePut putter, StorageGet getter) {
  assert(putter != NULL);
  assert(getter != NULL);
  storage_put_ = putter;
  storage_get_ = getter;
}

void Agent::AddPeers(const char *zmq_str, int num_peers) {
}

void Agent::RemovePeers(const char *zmq_str, int num_peers) {
}

void Agent::SetUniquePeerNumber(int n) {
}

void Agent::AddBind(const char *zmq_str) {
}

void Agent::RemoveBind(const char *zmq_str) {
}

void Agent::Start(bool recover) {
}

void Agent::Submit(const char *value, int value_len) {
}

}  // namespace LowLevel
}  // namespace LibConsent
