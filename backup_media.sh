#!/usr/bin/env bash
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=zsh

if mounts | grep \/dev\/mapper\/media1 &> /dev/null; then
else
    echo "ERROR: media1 does not seem to be mounted and cannot be backed up FROM"
    exit 1
fi

if mounts | grep \/dev\/mapper\/media2 &> /dev/null; then
else
    echo "ERROR: media2 does not seem to be mounted and cannot be backed up TO"
    exit 1
fi

echo "INFO: starting backing up media1 to media2"

rsync -ah --dry-run --filter "+ /movies/***" --filter "+ /music/***" --filter "+ /television/***" --filter "- *" --delete --delay-updates /mnt/media1/ /mnt/media2/
# rsync -ah --filter "+ /movies/***" --filter "+ /music/***" --filter "+ /television/***" --filter "- *" --delete --delay-updates /mnt/media1/ /mnt/media2/

echo "INFO: finishing backing up media1 to media2"
