# Distributions that want to compile with their hand-picked compile flags
# can simply set DIST_EXTRA_CPPFLAGS.

# Assert level can be one of three values: HARD, LOG, NONE
# HARD => halt on assertion failure
# LOG => log backtrace but proceed; in this case do something like:
#   -DLIBCONSENT_ASSERT_LOG_=\"filename_to_log_to\"
#   Note, logging only works with GNU libstdc++.
# NONE => no assertion checking
ASSERTLEVEL = -DLIBCONSENT_ASSERT_HARD_

CFLAGS = -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fno-exceptions \
	 -fstack-protector --param=ssp-buffer-size=4 -mtune=generic -flto \
	 -fpic -rdynamic
BUILDFLAGS = -std=c++0x $(CFLAGS) $(DIST_EXTRA_CPPFLAGS)
CC = g++

SRCS = agent.cc \
       agentinterface.cc \
       util.cc
OBJS = $(SRCS:.cc=.o)

all: libconsent.so libconsent.a

%.o:%.cc
	$(CC) $(BUILDFLAGS) $(ASSERTLEVEL) -c $<

libconsent.so: $(OBJS)
	$(CC) -shared -Wl,-soname,libconsent.so.0 -rdynamic -o $@ $(OBJS)

libconsent.a: $(OBJS)
	ar rcs $@ $(OBJS)

clean:
	rm -f *.o *.so *.a
