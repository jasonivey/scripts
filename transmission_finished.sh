#!/usr/bin/env bash
# vim: aw=on:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=sh
# autowrite, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype
SERVER="9091 --auth transmission:transmission"

torrent_id_count=`transmission-remote $SERVER --list | sed -e '1d;$d;s/^ *//' | awk '{ print $1 }' | wc -l`
count=$(expr $count + 0)
syslog -s -l 0 "POST TRANSMISSION: After that last torrent finished there are '$count' torrents left"

# Shutdown tranmission and eventually MacBook Pro
if [ $count -eq 0 ]; then
    syslog -s -l 0 "POST TRANSMISSION: shutting down the transmission app because $count == 0?"
    #transmission-remote $(SERVER) --exit
    syslog -s -l 0 "POST TRANSMISSION: sleeping for 10 seconds because $count == 0?"
    sleep 10
    syslog -s -l 0 "POST TRANSMISSION: shutting down the computer because $count == 0?"
    # Shut down after showing a confirmation dialog:
    osascript -e 'tell app "loginwindow" to «event aevtrsdn»'
fi

