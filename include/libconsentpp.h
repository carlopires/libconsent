// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#ifndef INCLUDE_LIBCONSENTPP_H_
#define INCLUDE_LIBCONSENTPP_H_

#include <cstdint>
#include <cstdlib>

// This macro is borrowed from Google's C++ style guide, which places code
// under the Perl license (GPL or Artistic). I think the terms of the Artistic
// license are liberal enough for me to distribute this trivial snippet with
// my MIT-licensed project; I'm pretty confident Google doesn't have a problem
// with it.
//
// A macro to disallow the copy constructor and operator= functions
// This should be used in the private: declarations for a class
#ifndef DISALLOW_COPY_AND_ASSIGN
# define DISALLOW_COPY_AND_ASSIGN(TypeName) \
  TypeName(const TypeName&); \
  void operator=(const TypeName&)
#endif

namespace LibConsent {

// LogCallbacks are used by paxos agents to inform users that consensus
// has been reached on a new value. They will only be called once for a given
// log number (history sequencing number).
//
// Log numbers start at 0; however, transient network errors can cause us to
// miss log entries. If a client receives an out of order log number, it is
// up to them to retrieve the missing log entries from other paxos agents.
typedef struct {
  int value_len;
  int proposer_num;
  char *value;

  int64_t log_num;
} LogEntry;
typedef void (*LogCallback)(LogEntry *entry);

// Helper types for user-provided storage functions.
//   Put(k, v) should only return when the user is sure the (k, v) pair is
// stored in a sufficiently stable fashion as required by the user.
// It returns false when it determines it cannot store the pair with the
// desired stability (e.g., when the disk is full).
//   Get(k) should copy the value into a freshly-malloc()ed buffer and
// return the pointer to the library. The library will free the buffer when
// no longer needed. It returns false when it cannot retrieve the
// corresponding value.
typedef bool (*StoragePut)(const char *key, size_t key_len,
    const char *value, size_t value_len);
typedef bool (*StorageGet)(const char *key, size_t key_len,
    char **value, size_t *value_len);

class AgentInterface;

// Agent_New creates a paxos agent (and starts its own thread). Will not
// actually participate in paxos until AgentInterface::Start() is called.
AgentInterface *Agent_New();

// Agent is an opaque handle to a paxos agent. It's used to manage the
// lifespan of an agent in paxos.
class AgentInterface {
 public:
  virtual ~AgentInterface();
  virtual void set_log_callback(LogCallback callback) = 0;
  virtual void set_storage_callbacks(StoragePut putter, StorageGet getter) = 0;

  // Set the timeout to use before assuming a response has failed; should be
  // something like the RTT between this node and the worst peer. Units of
  // nanoseconds. Obviously this will only be as accurate as the underlying
  // operating system timing mechanism. Only non-negative values are valid.
  virtual int message_timeout_interval() = 0;
  virtual void set_message_timeout_interval(int t) = 0;

  // Get the percentage of expected messages which timeout. Useful for tuning
  // the message timeout interval.
  virtual double get_timeout_percent() = 0;

  // Set/get the number of peers participating in paxos.
  virtual void set_num_peers(int n) = 0;
  virtual int num_peers() = 0;

  // Set the peer number of this peer; it must be a unique number `n' s.t.
  // 0 <= n < m, where `m' is the number of paxos peers participating in this
  // replicated log.
  virtual int unique_peer_number() = 0;
  virtual void set_unique_peer_number(int n) = 0;

  // Set/get the zeromq endpoint for each peer in paxos (including yourself).
  // In case it wasn't already obvious, zmq_endpoint should be a valid ZeroMQ
  // endpoint.
  virtual void set_peer_endpoint(int peer_number, const char *zmq_endpoint) = 0;
  virtual const char *peer_endpoint(int peer_number) = 0;

  // Add/remove zeromq multicast endpoints for broadcasting to peers
  // (performance optimization).
  // - If no multicast endpoints are configured, libconsent will fall back on
  //   point-to-point communication for message broadcast.
  // - If one or more multicast endpoint is configured, libconsent will
  //   broadcast on all of them.
  virtual void add_multicast_endpoint(const char *zmq_endpoint) = 0;
  virtual void remove_multicast_endpoint(const char *zmq_endpoint) = 0;

  // Start this paxos agent.
  // Preconditions:
  //   - The number of paxos peers has been configured and is > 2.
  //   - The unique peer number for this peer has been configured.
  //   - Every paxos peer has an endpoint configured.
  //   - The Agent has callbacks registered for incoming log entries, as
  //     well as putting/getting from stable storage.
  // Postconditions:
  //   - No more calls to any method named_like_this() (no run-time re-
  //     configuration yet, sorry).
  virtual void Start() = 0;

  // Asynchronously submits a value to log. May silently fail; clients
  // should monitor the LogCallback and resubmit themselves.
  //
  // Caveat: For efficiency purposes, users should arrange to have a master
  // Agent and only submit with it. (There is some latency per-election, and
  // each new Agent that wants to submit must become leader first.)
  virtual void Submit(const char *value, int value_len) = 0;

 protected:
  AgentInterface() {}

 private:
  DISALLOW_COPY_AND_ASSIGN(AgentInterface);
};

}  // namespace LibConsent

#endif  // INCLUDE_LIBCONSENTPP_H_
