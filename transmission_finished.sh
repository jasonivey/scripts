#!/usr/bin/env bash
# vim: aw:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=sh

SERVER="127.0.0.1:9091 --auth admin:admin"
SLEEP_TIME=10
APP_NAME="/usr/local/bin/transmission-remote"
SED_APP="/usr/local/bin/gsed"
AWK_APP="/usr/local/bin/awk"
WC_APP="/usr/local/bin/gwc"

sleep 5

torrent_id_count=`$APP_NAME $SERVER --list | $SED_APP -e '1d;$d;s/^ *//' | $AWK_APP '{ print $1 }' | $WC_APP -l | $SED_APP -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'`
torrent_id_count=$(expr $torrent_id_count + 0)

syslog -s -l 0 "POST TRANSMISSION: A torrent just finished. That leaves $torrent_id_count torrent(s) left."

# Shutdown tranmission and eventually MacBook Pro
if (( $torrent_id_count == 0 )); then
    syslog -s -l 0 "POST TRANSMISSION: The transmission count was $torrent_id_count. This means the transmission client will shutdown, sleep for $SLEEP_TIME seconds and request a computer shutdown."
    syslog -s -l 0 "POST TRANSMISSION: Shutting down the transmission app since the torrent count is $torrent_id_count."
    cmd="$APP_NAME $SERVER --exit"
    $cmd
    syslog -s -l 0 "POST TRANSMISSION: Sleeping for $SLEEP_TIME seconds to wait for transmission to exit since the torrent count is $torrent_id_count."
    sleep $SLEEP_TIME
    syslog -s -l 0 "POST TRANSMISSION: Requesting a shutdown of the computer since the torrent count is $torrent_id_count. This can be cancelled within the conofirmation window."
    osascript -e 'tell app "loginwindow" to «event aevtrsdn»'
else
    syslog -s -l 0 "POST TRANSMISSION: Not doing anything while there are still $torrent_id_count torrent(s) running."
fi

