// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#ifdef LIBCONSENT_ASSERT_LOG_
# include <execinfo.h>
#endif

#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "./util.h"

namespace LibConsent {

#ifdef LIBCONSENT_ASSERT_LOG_
void assert_log(int fd, const char *assertion, const char *file_name,
    int line_num, const char *func) {
  char buf[256];
  void *traces[64];

  snprintf(buf, sizeof buf, ">>> %s:%d: Assertion `%s' failed in `%s':\n",
      file_name, line_num, assertion, func);
  buf[sizeof buf - 1] = '\0';

  if (write(fd, buf, strlen(buf)) == -1) return;

  int num_traces = backtrace(traces, ARRAY_LEN(traces));
  backtrace_symbols_fd(traces, num_traces, fd);
  fdatasync(fd);
}
#endif

}  // namespace LibConsent
