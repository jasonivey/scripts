#!/usr/bin/env bash
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120:ft=sh

#function test_unicode_char_width {
#    stdbuf -o 0 echo -ne "$1\033[6n\033[1K\r"
#    read -d R foo
#    stdbuf -o 0 echo -ne "\003[1K\r"
#    stdbuf -o 0 echo -e "${foo}" | cut -d \[ -f 2 | cut -d";" -f 2 | (
#        read WIDTH
#        [ $WIDTH -eq $2 ] && return 0
#        [ $WIDTH -ne $2 ] && return 1
#    )
#}

#function test_unicode {
#    local latin_small_letter_e_with_acute="\xc3\xa9"  # should be 1 column wide for é character
#    local hiragana_letter_a="\xe3\x81\x82"            # should be 2 columns wide for あ character
#    local latin_support=false
#    local unicode_support=false
#    local character_map=()
#    local character_map+=("$latin_small_letter_e_with_acute" 1)
#    local character_map+=("$hiragana_letter_a" 2)
#    for i in "${character_map[@]}"
#    do
        # break $i into the touple that it was putting the pieces in $1 and $2
#        set -- $i
        # inserting it into a touple converted the integer to a string -- get an integer back
#        local column_count=$(($2 + 0))

        # test each unicode character and make sure the cursor moved the 'column count'
#        test_unicode_char_width "$1" $column_count
#        RC=$?
#        if [ $? -eq 0 ]; then
#            [ $column_count -eq 1 ] && latin_support=true
#            [ $column_count -eq 2 ] && unicode_support=true
#        fi
#    done

#    if [ $latin_support ]; then
#        echo -e "LATIN SUPPORT: yes ($latin_small_letter_e_with_acute)"
#    else
#        echo "LATIN SUPPORT: no"
#    fi
#    if [ $unicode_support ]; then
#        echo -e "UNICODE SUPPORT: yes ($hiragana_letter_a)"
#    else
#        echo "UNICODE SUPPORT: no"

#    fi
#}

test_unicode() {
    text='Éé'  # UTF-8; shows up as ÃÃ© on a latin1 terminal
    csi='␛['; dsr_cpr="${csi}6n"; dsr_ok="${csi}5n"  # ␛ is an escape character
    stty_save=`stty -g`
    cleanup () { stty "$stty_save"; }
    trap 'cleanup; exit 120' 0 1 2 3 15     # cleanup code
    stty eol 0 eof n -echo                # Input will end with `0n`
    # echo-n is a function that outputs its argument without a newline
    echo -n "$dsr_cpr$dsr_ok"              # Ask the terminal to report the cursor position
    initial_report=`{ { tr -dc \;0123456789 1>&3; kill 0; } | { sleep 2; kill 0; } } 3>&1`
    #initial_report=`sh -ic 'tr -dc \;0123456789 3>&1 2>/dev/null; { cat 1>&3; kill 0; } | { sleep 2; kill 0; }'`
    #initial_report=`tr -dc \;0123456789`  # Expect ␛[42;10R␛[0n for y=42,x=10
    echo -n "$text$dsr_cpr$dsr_ok"
    final_report=`{ { tr -dc \;0123456789 1>&3; kill 0; } | { sleep 2; kill 0; } } 3>&1`
    #final_report=`sh -ic 'tr -dc \;0123456789 3>&1 2>/dev/null; { cat 1>&3; kill 0; } | { sleep 2; kill 0; }'`
    #final_report=`tr -dc \;0123456789`
    cleanup
    #[[ "inital_x" == "final_x" ]] && echo 0 || echo 1
    echo "inital report: $initial_report"
    echo "final report:  $final_report"
    # Compute and return initial_x - final_x
}

test_unicode_1() {
}

test_unicode
unset test_unicode
