#!/usr/bin/env bash
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120:ft=sh

function test_unicode_char_width {
    stdbuf -o 0 echo -ne "$1\033[6n\033[1K\r"
    read -d R foo
    stdbuf -o 0 echo -ne "\003[1K\r"
    stdbuf -o 0 echo -e "${foo}" | cut -d \[ -f 2 | cut -d";" -f 2 | (
        read WIDTH
        [ $WIDTH -eq $2 ] && return 0
        [ $WIDTH -ne $2 ] && return 1
    )
}

function test_unicode {
    local latin_small_letter_e_with_acute="\xc3\xa9"  # should be 1 column wide for é character
    local hiragana_letter_a="\xe3\x81\x82"            # should be 2 columns wide for あ character
    local latin_support=false
    local unicode_support=false
    local character_map=()
    local character_map+=("$latin_small_letter_e_with_acute" 1)
    local character_map+=("$hiragana_letter_a" 2)
    for i in "${character_map[@]}"
    do
        # break $i into the touple that it was putting the pieces in $1 and $2
        set -- $i
        # inserting it into a touple converted the integer to a string -- get an integer back
        local column_count=$(($2 + 0))

        # test each unicode character and make sure the cursor moved the 'column count'
        test_unicode_char_width "$1" $column_count
        RC=$?
        if [ $? -eq 0 ]; then
            [ $column_count -eq 1 ] && latin_support=true
            [ $column_count -eq 2 ] && unicode_support=true
        fi
    done

    if [ $unicode_support ]; then
        echo "UNICODE SUPPORT: yes"
    else
        echo "UNICODE SUPPORT: no"

    fi
    if [ $latin_support ]; then
        echo "LATIN SUPPORT: yes"
    else
        echo "LATIN SUPPORT: no"
    fi
}

test_unicode
unset test_unicode
