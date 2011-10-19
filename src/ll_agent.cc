// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#include <sys/types.h>
#include <sys/stat.h>

#include <assert.h>
#include <fcntl.h>

#include <pthread.h>

#include "../include/libconsentpp.h"
#include "./ll_agent.h"
#include "./util.h"

namespace LibConsent {
namespace LowLevel {

Agent::Agent() : zmq_(new zmqmm::context_t(1)) {
  log_callback_ = NULL;
  storage_put_ = NULL;
  storage_get_ = NULL;
  unique_peer_number_ = -1;
  message_timeout_interval_ = -1;
  stats_messages_expected_ = 0;
  stats_messages_received_ = 0;
  num_peers_ = 1;

  pthread_rwlock_init(&rwlock_, NULL);
#ifdef LIBCONSENT_ASSERT_LOG_
  assert_log_fd_ =
    open(LIBCONSENT_ASSERT_LOG_, O_APPEND|O_CREAT|O_WRONLY, 0644);
  assert(assert_log_fd_ != -1);
#endif
}

void Agent::set_log_callback(LogCallback callback) {
  LC_ASSERT(callback != NULL);

  pthread_rwlock_wrlock(&rwlock_);
  log_callback_ = callback;
  pthread_rwlock_unlock(&rwlock_);
}

void Agent::set_storage_callbacks(StoragePut putter, StorageGet getter) {
  LC_ASSERT(putter != NULL);
  LC_ASSERT(getter != NULL);

  pthread_rwlock_wrlock(&rwlock_);
  storage_put_ = putter;
  storage_get_ = getter;
  pthread_rwlock_unlock(&rwlock_);
}

int Agent::unique_peer_number() {
  int res;

  pthread_rwlock_rdlock(&rwlock_);
  res = unique_peer_number_;
  pthread_rwlock_unlock(&rwlock_);

  return res;
}

void Agent::set_unique_peer_number(int n) {
  LC_ASSERT(n >= 0);

  pthread_rwlock_wrlock(&rwlock_);
  unique_peer_number_ = n;
  pthread_rwlock_unlock(&rwlock_);
}

int Agent::message_timeout_interval() {
  int res;

  pthread_rwlock_rdlock(&rwlock_);
  res = message_timeout_interval_;
  pthread_rwlock_unlock(&rwlock_);

  return res;
}

void Agent::set_message_timeout_interval(int t) {
  LC_ASSERT(t > 0);

  pthread_rwlock_wrlock(&rwlock_);
  message_timeout_interval_ = t;
  pthread_rwlock_unlock(&rwlock_);
}

double Agent::get_timeout_percent() {
  int64_t expected, received;

  pthread_rwlock_rdlock(&rwlock_);
  expected = stats_messages_expected_;
  received = stats_messages_received_;
  pthread_rwlock_unlock(&rwlock_);

  if (!expected) return 0.0;
  double timedout = expected - received;
  return timedout / expected;
}

void Agent::AddPeers(const char *zmq_str, int num_peers) {
  LC_ASSERT(num_peers > 0);
}

void Agent::RemovePeers(const char *zmq_str, int num_peers) {
  LC_ASSERT(num_peers > 0);
}

void Agent::AddBind(const char *zmq_str) {
}

void Agent::RemoveBind(const char *zmq_str) {
}

void Agent::Start(bool recover) {
  LC_ASSERT(log_callback_);
  LC_ASSERT(storage_put_);
  LC_ASSERT(storage_get_);
  LC_ASSERT(unique_peer_number_ >= 0);
  LC_ASSERT(message_timeout_interval_ >= 0);
  LC_ASSERT(unique_peer_number_ < num_peers_);
  LC_ASSERT(num_peers_ > 2);
}

void Agent::Submit(const char *value, int value_len) {
  LC_ASSERT(value_len >= 0);

  // TODO(conrad): this will create a sock, connect to inproc://agent-submit or
  // similar, thereby signalling the Start() thread to submit a new value.
}

}  // namespace LowLevel
}  // namespace LibConsent
