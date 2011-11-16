#!/bin/bash

# Put as many distinctly-named replicas as you want here (N > 0):
replicas=( alice bob cait )
acclist=""
othlist=""

# Construct the list of replica acceptors, others:
for repl in "${replicas[@]}" ; do
  acclist="${acclist},ipc://${repl}-acc"
  othlist="${othlist},ipc://${repl}-learn,ipc://${repl}-prop"
done
acclist="${acclist:1}"
othlist="${othlist:1}"

# Bring up the replicas:
xmlrpcport=8888
echo "Binding ${xmlrpcport} and up for RPCs."
for repl in "${replicas[@]}" ; do
  python3 replica.py "backing_${repl}.db" "127.0.0.1:${xmlrpcport}"  \
    "ipc://${repl}-acc" \
    "ipc://${repl}-learn" \
    "ipc://${repl}-prop" \
    "${othlist}" \
    "${acclist}" &

  xmlrpcport=$((xmlrpcport+1))
done

function usage(){
  echo "  Usage:"
  echo "    propose <p> <v> - Propose value v"
  echo "    learn <p>       - Check learned value"
  echo "    exit|quit       - Quit"
  echo "  <p> is the port to send the rpc to"
  echo "  <v> is the value"
  echo ""
}

echo "Paxos implementation tool:"
usage

while read -p "> " line; do
  spacepos=$(expr index "$line" " ")
  cmd="$line"
  rest=""
  if [ $spacepos -gt 0 ]; then
    cmd="${line:0:$((spacepos-1))}"
    rest="${line:$spacepos}"
  fi

  value=""
  spacepos=$(expr index "$rest" " ")
  if [ $spacepos -gt 0 ]; then
    value="${rest:$spacepos}"
    rest="${rest:0:$((spacepos-1))}"
  fi

  case "$cmd" in
    propose )
      if [ "x$rest" = "x" -o "x$value" = "x" ]; then
        usage
      else
        python3 xmlrpc_helper.py "http://127.0.0.1:$rest" propose "$value"
      fi
      ;;
    learn )
      if [ "x$rest" = "x" ]; then
        usage
      else
        python3 xmlrpc_helper.py "http://127.0.0.1:$rest" value
      fi
      ;;
    exit ) break
      ;;
    quit ) break
      ;;
    * ) usage
      ;;
  esac
done

# Kill the replicas when we're done.
kill %1 %2 %3
for repl in "${replicas[@]}" ; do
  rm "backing_${repl}.db"
  rm "${repl}-acc" # zmq sockets
  rm "${repl}-learn"
  rm "${repl}-prop"
done
