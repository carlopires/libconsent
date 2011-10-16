// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#include "../include/libconsentpp.h"
#include "./ll_agent.h"

namespace LibConsent {
namespace LowLevel {

AgentInterface *Agent_New() {
  return new Agent();
}

AgentInterface::~AgentInterface() {
}

}  // namespace LowLevel
}  // namespace LibConsent
