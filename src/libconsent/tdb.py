# Copyright 2011 Conrad Meyer <cemeyer@uw.edu>
#
# This work is placed under the MIT license, the full text of which is
# included in the `COPYING' file at the root of the project sources.
#
# Author(s): Conrad Meyer
#
# A trivial implementation of the database required for using libconsent's
# paxos implementation. Depends on 'shelve' for atomic and durable storage;
# this is probably not good enough if you care about resilience.

import shelve

class _tdb:
  def __init__(self, fn):
    self._db = shelve.open(fn)

  def get(self, key, defval=None):
    if key in self._db:
      return self._db[key]
    return defval

  def put(self, key, value):
    self._db[key] = value
    self._db.sync()

def open(fn):
  """
  Opens a trivial database at the given filename 'fn'. It will create the file
  if it does not exist, or load from the file if it does exist.
  """
  return _tdb(fn)
