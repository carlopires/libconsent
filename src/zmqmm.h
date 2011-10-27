// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer
//
// Incomplete (API-wise), exception-free ZMQ API for C++.

#ifndef SRC_ZMQMM_H_
#define SRC_ZMQMM_H_

#include <assert.h>

#include <zmq.h>

namespace zmqmm {

class context_t {
 public:
  explicit context_t(int num_threads) {
    zmq_ = zmq_init(num_threads);
    assert(zmq_);
  }
  ~context_t() {
    int s;
    do {
      s = zmq_term(zmq_);
    } while (s == -1 && errno == EINTR);
  }
  void *context() { return zmq_; }

 private:
  void *zmq_;
};

class message_t {
 public:
  message_t() { zmq_msg_init(&msg_); }
  explicit message_t(size_t size) {
    int s = zmq_msg_init_size(&msg_, size);
    assert(s != -1);
  }
  ~message_t() {
    int s = zmq_msg_close(&msg_);
    assert(s != -1);
  }
  zmq_msg_t *msg() { return &msg_; }
  void *data() { return zmq_msg_data(&msg_); }
  size_t size() { return zmq_msg_size(&msg_); }
  void reinit() {
    int s = zmq_close(&msg_);
    assert(s != -1);
    zmq_msg_init(&msg_);
  }

 private:
  zmq_msg_t msg_;
};

class socket_t {
 public:
  socket_t() {}
  socket_t(context_t *ctx, int type) {
    int s = init(ctx->context(), type);
    assert(s != -1);
  }
  int init(void *context, int type) {
    socket_ = zmq_socket(context, type);
    return socket_? 0 : -1;
  }
  ~socket_t() {
    int s = zmq_close(socket_);
    assert(s != -1);
  }
  int setsockopt(int option_name, const void *option_value, size_t option_len) {
    int s;
    do {
      s = zmq_setsockopt(socket_, option_name, option_value, option_len);
    } while (s == -1 && errno == EINTR);
    return s;
  }
  int getsockopt(int option_name, void *option_value, size_t *option_len) {
    int s;
    do {
      s = zmq_getsockopt(socket_, option_name, option_value, option_len);
    } while (s == -1 && errno == EINTR);
    return s;
  }
  int bind(const char *endpoint) {
    return zmq_bind(socket_, endpoint);
  }
  int connect(const char *endpoint) {
    return zmq_connect(socket_, endpoint);
  }
  int send(message_t *msg, int flags) {
    int s;
    do {
      s = zmq_send(socket_, msg->msg(), flags);
    } while (s == -1 && errno == EINTR);
    return s;
  }
  int recv(message_t *msg, int flags) {
    int s;
    do {
      s = zmq_recv(socket_, msg->msg(), flags);
    } while (s == -1 && errno == EINTR);
    return s;
  }

 private:
  void *socket_;
};

}  // namespace zmqmm

#endif  // SRC_ZMQMM_H_
