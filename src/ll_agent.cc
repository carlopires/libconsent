#include <libconsent++>

#include "ll_agent.h"

namespace LibConsent {
namespace LowLevel {

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
