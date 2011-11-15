#!/bin/bash

# Terminal log showing this script in use:
#
# $ bash part1_test.bash
#   Paxos implementation tool:
#     Usage:
#       propose <r> <v> - Propose value v
#       learn <r>       - Check learned value
#       exit|quit       - Quit
#     <r> is the replica name to send the rpc to
#     <v> is the value
#
#   > propose alice test1
#   None
#   > propose bob test2
#   None
#   > propose charlie test3
#   None
#   > propose alice test4
#   None
#   > learn bob
#   ('KNOW', 'test1')
#   > exit
#
# Another:
#   $ bash part1_test.bash
#   Paxos implementation tool:
#     Usage:
#       propose <r> <v> - Propose value v
#       learn <r>       - Check learned value
#       exit|quit       - Quit
#     <r> is the replica name to send the rpc to
#     <v> is the value
#
#   > learn alice
#   ('DONT_KNOW',)
#   >

# Put as many distinctly-named replicas as you want here (N > 0):
replicas=( alice bob charlie )
peerlist=""

# Construct the list of replica peers:
for repl in "${replicas[@]}" ; do
  peerlist="${peerlist},ipc://${repl}"
done
peerlist="${peerlist:1}"

# Bring up the replicas:
for repl in "${replicas[@]}" ; do
  python3 replica.py "backing_${repl}.db" "ipc://${repl}" \
    "${peerlist}" &
done

function usage(){
  echo "  Usage:"
  echo "    propose <r> <v> - Propose value v"
  echo "    learn <r>       - Check learned value"
  echo "    exit|quit       - Quit"
  echo "  <r> is the replica name to send the rpc to"
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
        python3 rpc_tool.py "ipc://$rest" propose "$value"
      fi
      ;;
    learn )
      if [ "x$rest" = "x" ]; then
        usage
      else
        python3 rpc_tool.py "ipc://$rest" learn
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
  rm "${repl}" # zmq sockets
done
