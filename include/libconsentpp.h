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
namespace LowLevel {

// LogCallbacks are used by paxos agents to inform users that consensus
// has been reached on a new value. They will only be called once for a given
// log number (history sequencing number), although there may be duplicates
// on restart.
typedef struct {
  char *value;
  int value_len;

  int64_t log_num;
} LogEntry;
typedef void (*LogCallback)(LogEntry *entry);

// Helper types for user-provided storage functions.
//   Put(k, v) should only return when the user is sure the (k, v) pair is
// stored in a sufficiently stable fashion as required by the user.
//   Get(k) should copy the value into a freshly-malloc()ed buffer and
// return the pointer to the library. The library will free the buffer when
// no longer needed.
typedef void (*StoragePut)(const char *key, size_t key_len,
    const char *value, size_t value_len);
typedef void (*StorageGet)(const char *key, size_t key_len,
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

  // Set the peer number of this peer; it must be a unique number `n' s.t.
  // 0 <= n < m, where `m' is the number of paxos peers participating in this
  // replicated log.
  virtual int unique_peer_number() = 0;
  virtual void set_unique_peer_number(int n) = 0;

  // Set the timeout to use before assuming a response has failed; should be
  // something like the RTT between this node and the worst peer. Units of
  // nanoseconds.
  virtual int message_timeout_interval() = 0;
  virtual void set_message_timeout_interval(int t) = 0;

  // Get the percentage of expected messages which timeout. Useful for tuning
  // the message timeout interval.
  virtual double get_timeout_percent() = 0;

  // Inform the paxos agent of some peers accessible at some ZeroMQ URI.
  // num_peers should be strictly positive. (It must be 1 unless the URI
  // refers to a multicast transport.)
  virtual void AddPeers(const char *zmq_str, int num_peers) = 0;
  virtual void RemovePeers(const char *zmq_str, int num_peers) = 0;

  // Inform the paxos agent how it can recieve messages from other peers:
  virtual void AddBind(const char *zmq_str) = 0;
  virtual void RemoveBind(const char *zmq_str) = 0;

  // Attempts to start a paxos agent. Unless `recover' is false, tries to
  // recover (under the assumption the agent failed and is restarting).
  // Preconditions:
  //   - The Agent has been bound to at least one zmq socket (AddBind())
  //   - The Agent has >= 2 peers configured
  //   - The Agent has callbacks registered for incoming log entries, as
  //     well as putting/getting from stable storage.
  //   - The Agent has a unique peer number configured.
  // Runs forever.
  virtual void Start(bool recover) = 0;

  // Asynchronously submits a value to log. May silently fail; clients
  // should monitor the LogCallback and resubmit themselves.
  //
  // Caveat: For efficiency purposes, users should arrange to have a master
  // Agent and only submit with it.
  virtual void Submit(const char *value, int value_len) = 0;

 protected:
  AgentInterface() {}

 private:
  DISALLOW_COPY_AND_ASSIGN(AgentInterface);
};

}  // namespace LowLevel
}  // namespace LibConsent

#endif  // INCLUDE_LIBCONSENTPP_H_
