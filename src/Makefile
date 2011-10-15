# Distributions that want to compile with their hand-picked compile flags
# can simply set DIST_EXTRA_CPPFLAGS.

CFLAGS = -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -mtune=generic -flto -fpic
BUILDFLAGS = $(CFLAGS) -std=c++0x $(DIST_EXTRA_CPPFLAGS)
CC = g++

SRCS = ll_agent.cc
OBJS = $(SRCS:.cc=.o)

all: libconsent.so.0

%.o:%.cc
	$(CC) $(BUILDFLAGS) -c $<

libconsent.so.0: $(OBJS)
	$(CC) -shared -Wl,-soname,libconsent.so.0 -o $@ $(OBJS)

clean:
	rm -f *.o *.so.*
