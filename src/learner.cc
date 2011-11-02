// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#include "./acceptor.h"
#include "./learner.h"
#include "./paxos.pb.h"
#include "./util.h"

namespace LibConsent {

int Learner::Init(Agent *agent, zmqmm::context_t *zmq, Acceptor *acceptor,
    LogCallback callback) {
  if (listen_socket_.init(zmq, ZMQ_SUB) == -1) return -1;
  if (listen_socket_.connect(acceptor->output_endpoint().c_str()) == -1)
    return -1;
  if (listen_socket_.setsockopt(ZMQ_SUBSCRIBE, NULL, 0) == -1) return -1;

  callback_ = callback;

  return 0;
}

static void *LearnerRun(void *learner_) {
  Learner *learner = reinterpret_cast<Learner *>(learner_);
  zmqmm::message_t msg;
  AcceptorLearnerPacketHeader header;
  LogEntry log_entry;

  int64_t more;
  size_t sz_more;

  while (true) {
    int s = learner->listen_socket_.recv(&msg, 0);
    if (s == -1) {
      switch (errno) {
        case ETERM:
          return NULL;
        default:
          LC_ASSERT(false);
      }
    }

    if (!header.ParseFromArray(msg.data(), msg.size())) {
      fprintf(stderr, "[ERROR] Learner got bad packet from Acceptor\n");
      LC_ASSERT(false);
      goto clean_and_continue;
    }

    if (!header.has_proposer_id() || !header.has_log_number()) {
      fprintf(stderr, "[ERROR] Learner got packet missing fields\n");
      LC_ASSERT(header.has_proposer_id() && header.has_log_number());
      goto clean_and_continue;
    }

    msg.reinit();

    sz_more = sizeof more;
    s = learner->listen_socket_.getsockopt(ZMQ_RCVMORE, &more, &sz_more);
    if (s == -1) {
      switch (errno) {
        case ETERM:
          return NULL;
        default:
          LC_ASSERT(false);
      }
    }

    if (!more) {
      fprintf(stderr, "[ERROR] Learner got packet missing value\n");
      LC_ASSERT(more);
      goto clean_and_continue;
    }

    if ((s = learner->listen_socket_.recv(&msg, 0)) == -1) {
      switch (errno) {
        case ETERM:
          return NULL;
        default:
          LC_ASSERT(false);
      }
    }

    log_entry.value_len = msg.size();
    log_entry.proposer_num = header.proposer_id();
    log_entry.value = msg.data();
    log_entry.log_num = header.log_number();

    learner->callback_(&log_entry);

 clean_and_continue:
    header.Clear();
    msg.reinit();
  }
}

void Learner::Start() {
  pthread_t thread_id;
  int s = pthread_create(&thread_id, NULL, LearnerRun,
      reinterpret_cast<void *>(this));
  LC_ASSERT(s == 0);
}

}  // namespace LibConsent
