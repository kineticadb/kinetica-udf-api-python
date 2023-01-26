#! /usr/bin/env bash

# This script uses ssh to connect to all hosts in the cluster to
# manage packages availble to Python UDFs by running pip3 with the provided args.
# The packages are installed to /opt/gpudb/python3/lib/python3.7/site-packages/...
# Usage  : ./gpudb-pip.sh [ARGS to pip...]
# Example: ./gpudb-pip.sh install requests pytz ...

GPUDB_DIR=/opt/gpudb

$GPUDB_DIR/core/bin/gpudb_hosts_ssh_execute.sh $GPUDB_DIR/core/bin/gpudb_env.sh pip3 "$@"
