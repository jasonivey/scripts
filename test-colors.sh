#!/usr/bin/env bash
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

for i in {0..255} ; do
    printf "\x1b[38;5;${i}m%3d " "${i}"
    if (( $i < 15 )) ; then
        continue;
    elif (( $i == 15 )) ; then
        echo;
    elif (( ($i - 15) % 12 == 0 )) ; then # (( (( (($i - 15)) % 12 )) == 0 )); then
        echo;
    fi
done
