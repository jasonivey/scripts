#! /bin/bash

declare -a ARGS=($@)
FILTER=$1
FILES=${ARGS[@]:1}

for x in $FILES;
do
    echo $x
    ffmpeg -y -debug_ts -i $x /tmp/foobar.mp4 2>&1 | grep $FILTER
done

