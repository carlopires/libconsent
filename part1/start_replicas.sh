# Use this by source'ing it into your current term.

for repl in alice bob cait ; do
  python3 replica.py "backing_${repl}.db" "ipc://${repl}" \
    ipc://alice,ipc://bob,ipc://cait &
done
