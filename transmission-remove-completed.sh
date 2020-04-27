#!/usr/bin/env bash

# the folder to move completed downloads to

# port, username, password
SERVER="9091 --auth transmission:transmission"

# use transmission-remote to get torrent list from transmission-remote list
# use sed to delete first / last line of output, and remove leading spaces
# use awk to pull the first field (the ID) from the input
TORRENT_IDS=`transmission-remote $SERVER --list | sed -e '1d;$d;s/^ *//' | awk '{ print $1 }'`

# for each torrent in the list
for TORRENT_ID in $TORRENT_IDS
do
    # Grab various details about the current torrent
    TORRENT_INFO=`transmission-remote $SERVER --torrent $TORRENT_ID --info`

    # Parse the raw data
    TORRENT_NAME=`grep "Name:\s*[^\s]*\s" <<< ${TORRENT_INFO} | awk '{ print $NF }'`
    TORRENT_PERCENTAGE=`grep "Percent Done:\s*[^\s]*%" <<< ${TORRENT_INFO} | awk '{ print $NF }'`
    TORRENT_STATE=`grep "State: [a-zA-Z]*" <<< ${TORRENT_INFO} | awk '{ print $NF }'`

    # Parse out what we will use to determine whether the torrent is finished
    TORRENT_DOWNLOADED=`grep "100%" <<< ${TORRENT_PERCENTAGE}`

    TORRENT_IS_COMPLETE=0
    TORRENT_IS_COMPLETE_STR="false"
    case $TORRENT_STATE in
        Seeding | Stopped | Finished | Idle )
            TORRENT_IS_COMPLETE=1
            TORRENT_IS_COMPLETE_STR="true" ;;
        *)
            TORRENT_IS_COMPLETE=0
            TORRENT_IS_COMPLETE_STR="false" ;;
    esac

    printf "Processing torrent %d, Name: %s, Percentage Done: %s, State: %s, Finished: %s\n" \
        $TORRENT_ID $TORRENT_NAME $TORRENT_PERCENTAGE $TORRENT_STATE $TORRENT_IS_COMPLETE_STR

    # if the torrent is not 100% complete or the state is not Seeding | Stopped | Finished | Idle
    if [[ "$TORRENT_DOWNLOADED" == "100%" ]] && [[ $TORRENT_IS_COMPLETE ]]; then
        # remove the torrent from transmission server
        echo "Removing #${TORRENT_ID}: ${TORRENT_NAME} since it is completed"
        transmission-remote ${SERVER} --torrent ${TORRENT_ID} --remove
        echo "Removed #${TORRENT_ID}: ${TORRENT_NAME} from transmission server"
    else
        # show the percent complete and move onto the next torrent in the list
        echo "Ignoring #${TORRENT_ID}: ${TORRENT_NAME} which is ${TORRENT_PERCENTAGE} completed and not finished"
    fi
done
