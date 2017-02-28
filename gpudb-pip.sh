#! /usr/bin/env bash

GPUDB_DIR=/opt/gpudb

$GPUDB_DIR/core/bin/gpudb_hosts_ssh_execute.sh $GPUDB_DIR/core/bin/gpudb_env.sh pip "$@"
