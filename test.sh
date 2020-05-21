#!/usr/bin/env bash
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120:ft=sh

function test_unicode {
    echo -ne "\xe2\x88\xb4\033[6n\033[1K\r"
    read -d R foo
    echo -ne "\003[1K\r"
    echo -e "${foo}" | cut -d \[ -f 2 | cut -d";" -f 2 | (
        read UNICODE
        [ $UNICODE -eq 2 ] && return 0
        [ $UNICODE -ne 2 ] && return 1
    )
}

test_unicode
RC=$?
export UNICODE_SUPPORT=`[ $RC -eq 0 ] && echo "Yes" || echo "No"`
unset test_unicode
