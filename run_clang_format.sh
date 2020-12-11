#!/usr/bin/env bash
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=sh

git ls-files | grep -e "^.*\.cpp$" -e "^.*\.h$" | while read filename
do
    clang-format -i --verbose $filename
done

