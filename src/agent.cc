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
#include <string.h>

#include <vector>

#include "../include/libconsentpp.h"
#include "./agent.h"
#include "./util.h"

namespace LibConsent {

Agent::Agent() : zmq_(1/*io_threads*/), broadcast_socket_(&zmq_, ZMQ_PUB),
  listen_socket_(&zmq_, ZMQ_SUB) {
  log_callback_ = NULL;
  storage_put_ = NULL;
  storage_get_ = NULL;
  unique_peer_number_ = -1;
  message_timeout_interval_ = -1;
  stats_messages_expected_ = 0;
  stats_messages_received_ = 0;
  num_peers_ = 0;

#ifdef LIBCONSENT_ASSERT_LOG_
  assert_log_fd_ =
    open(LIBCONSENT_ASSERT_LOG_, O_APPEND|O_CREAT|O_WRONLY, 0644);
  assert(assert_log_fd_ != -1);
#endif
}

void Agent::set_log_callback(LogCallback callback) {
  LC_ASSERT(callback != NULL);

  log_callback_ = callback;
}

void Agent::set_storage_callbacks(StoragePut putter, StorageGet getter) {
  LC_ASSERT(putter != NULL);
  LC_ASSERT(getter != NULL);

  storage_put_ = putter;
  storage_get_ = getter;
}

int Agent::message_timeout_interval() {
  return message_timeout_interval_;
}

void Agent::set_message_timeout_interval(int t) {
  LC_ASSERT(t > 0);

  message_timeout_interval_ = t;
}

double Agent::get_timeout_percent() {
  int64_t expected = stats_messages_expected_,
          received = stats_messages_received_;

  if (!expected) return 0.0;
  double timedout = expected - received;
  return timedout / expected;
}

void Agent::set_num_peers(int n) {
  LC_ASSERT(n > 0);

  num_peers_ = n;
  peer_endpoints_.resize(n);
}

int Agent::num_peers() {
  return num_peers_;
}

int Agent::unique_peer_number() {
  return unique_peer_number_;
}

void Agent::set_unique_peer_number(int n) {
  LC_ASSERT(n >= 0);
  LC_ASSERT(n < num_peers_);

  unique_peer_number_ = n;
}

void Agent::set_peer_endpoint(int peer_number, const char *zmq_endpoint) {
  LC_ASSERT(peer_number >= 0);
  LC_ASSERT(peer_number < num_peers_);
  LC_ASSERT(zmq_endpoint);

  peer_endpoints_[peer_number] = zmq_endpoint;
}

const char *Agent::peer_endpoint(int peer_number) {
  LC_ASSERT(peer_number >= 0);
  LC_ASSERT(peer_number < num_peers_);

  return peer_endpoints_[peer_number].c_str();
}

void Agent::add_multicast_endpoint(const char *zmq_endpoint) {
  LC_ASSERT(zmq_endpoint);

  multicast_endpoints_.insert(std::string(zmq_endpoint));
}

void Agent::remove_multicast_endpoint(const char *zmq_endpoint) {
  LC_ASSERT(zmq_endpoint);

  multicast_endpoints_.erase(std::string(zmq_endpoint));
}

void Agent::Start() {
  LC_ASSERT(log_callback_);
  LC_ASSERT(storage_put_);
  LC_ASSERT(storage_get_);
  LC_ASSERT(unique_peer_number_ >= 0);
  LC_ASSERT(message_timeout_interval_ >= 0);
  LC_ASSERT(unique_peer_number_ < num_peers_);
  LC_ASSERT(num_peers_ > 2);

  // TODO(Conrad) bring up sockets; verify that connect() succeeds on each
  // endpoint. Bring up state machines (one for acceptor, one for proposer).
}

void Agent::Submit(const char *value, int value_len) {
  LC_ASSERT(value_len >= 0);

  zmqmm::socket_t sock(&zmq_, ZMQ_PUB);
  if (sock.connect("inproc://agent-submit") == -1) return;
  zmqmm::message_t msg(value_len);
  memcpy(msg.data(), value, value_len);
  sock.send(&msg, 0);
}

}  // namespace LibConsent