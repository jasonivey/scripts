#!/usr/bin/env bash
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=bash
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

set -e

hide_mac_os_apps_in_dir() {
    search_dir=$1
    pushd $search_dir
    echo "search dir: $search_dir"
    for app_dir in *.app/; do
        full_path="$search_dir/$app_dir"
        echo "$full_path -- app"
        #printf '%s -- app\n' "$app_dir"
        #if output=$("SetFile -a E $app_dir"); then
        #    printf 'set file succeeded and hid $app_dir: %s\n' "$output"
        #else
        #    printf 'set file trying to hide $app_dir: %s\n' "$output"
        #fi
    done
    popd
}

function hide_mac_os_apps() {
    app_dirs=("/Applications" "/Users/jasoni/Applications")
    local count=${#app_dirs[@]}
    echo "apps dirs count: {$count}"
    for (( i=0; i<count; i++ )); do
        echo ${app_dirs[$i]}
        local -a -x app_dir=( "${app_dirs[i]}" )
        app_dir=${app_dir[i]}
        #app_dir="$app_dirs[$i]"
        #printf "processing dir: " "$app_dir"
        echo "processing dir: $app_dir"
        hide_mac_os_apps_in_dir $app_dir
        pushd $app_dir
        echo "checking for sub dirs in: $app_dir"
        find -depth 1 -type d
        for sub_dir in "/*"; do
            full_path="$app_dir/$subdir_dir"
            echo "Adding directory: $full_path"
            app_dirs+=("$subdir")
        done
        popd
        count=${#app_dirs[@]}
    done
}

hide_mac_os_apps
