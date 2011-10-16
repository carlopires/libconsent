// Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
//
// This work is placed under the MIT license, the full text of which is
// included in the `COPYING' file at the root of the project sources.
//
// Author(s): Conrad Meyer

#ifndef SRC_UTIL_H_
#define SRC_UTIL_H_

#include <assert.h>

#define ARRAY_LEN(__array) \
  (sizeof(__array) / sizeof(__array[0]))

// We define our own assertion macro, LC_ASSERT. Depending on the value of
// ASSERTLEVEL in the Makefile, this library can be built to handle assertion
// failures in a few different ways:
#if defined LIBCONSENT_ASSERT_HARD_
# define DEBUG 1
# undef NDEBUG
# define LC_ASSERT(__cond) assert(__cond)

#elif defined LIBCONSENT_ASSERT_LOG_
# warning Logging allows program flow to proceed despite assertion
# warning violation. Are you sure you want this?
namespace LibConsent {
extern void assert_log(int fd, const char *assertion, const char *file_name,
    int line_num, const char *func);
}
# define LC_ASSERT(__cond) do { \
  if (!(__cond)) { \
    LibConsent::assert_log(this->assert_log_fd_, __STRING(__cond), __FILE__, \
        __LINE__, __ASSERT_FUNCTION); \
  } \
} while (0)

#elif defined LIBCONSENT_ASSERT_NONE_
# warning Do you really want to turn off correctness checking?
# define LC_ASSERT(__cond) while (false)

#else
# error Must define one of LIBCONSENT_ASSERT_ {HARD, LOG, or NONE}_
# error HARD => halt on assert
# error LOG => log assertion failures
# error NONE => do not evaluate assertions
#endif

#endif  // SRC_UTIL_H_
