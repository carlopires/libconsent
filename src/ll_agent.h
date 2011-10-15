#ifndef LIBCONSENT_LL_AGENT_H_
#define LIBCONSENT_LL_AGENT_H_

#include <assert.h>

#include <libconsent++>

namespace LibConsent {
namespace LowLevel {

class Agent : AgentInterface {
public:
  virtual void set_log_callback(LogCallback callback) {
    assert(callback != NULL);
    log_callback_ = callback;
  }
  virtual void set_storage_callbacks(StoragePut putter, StorageGet getter) {
    assert(putter != NULL);
    assert(getter != NULL);
    storage_put_ = putter;
    storage_get_ = getter;
  }
  Agent() {
    log_callback_ = NULL;
    storage_put_ = NULL;
    storage_get_ = NULL;
  }
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
};

}  // namespace LowLevel
}  // namespace LibConsent

#endif  // LIBCONSENT_LL_AGENT_H_
