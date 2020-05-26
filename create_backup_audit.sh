#!/usr/bin/env bash
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=bash
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

set -e

VERBOSE=false
retval=0

function create_dir_audit {
    local audit_location="$1"
    local audit_destination="$2"
    pushd "$audit_location" > /dev/null 2>&1
    echo "audit location:    $audit_location"
    echo "audit destination: $audit_destination"
    if [ -f "$audit_destination" ]; then
        echo "ERROR: the audit destination file '$audit_destination' already exists -- not overwriting"
        retval=1
    else
        echo "Creating audit `pwd` and savnig to $audit_destination"
        hashdeep -l -r . > "$audit_destination"
        retval=$?
        if [ $retval -ne 0 ]; then
            echo "ERROR: hashdeep encountered error $retval in '$audit_location'"
        else
            local host=`hostname`
            local body="Finished audit for $audit_location (`pwd`) on $host and placed it in $audit_destination"
            local subject="Finished audit of $audit_location"
            echo "$body" | mail -s "$subject" jasonivey@gmail.com
            retval=$?
        fi
    fi
    popd > /dev/null 2>&1
}

function create_backup_audit {
    local -n retval1=$3
    echo "starting retval1: $retval1"
    local audit_dir=$1
    local output_dir=$2
    echo "dir: $1"
    echo "output dir: $2"
    pushd "$audit_dir" > /dev/null 2>&1
    find . -mindepth 1 -maxdepth 1 -type d | while read dirname; do
        dirname=${dirname:2}
        local file_name=$(printf "hash-%s.txt" $(echo "${dirname// /-}" | tr '[:upper:]' '[:lower:]'))
        local output_file="$output_dir/$file_name"
        echo "Creating audit: '$dirname'"
        echo "Saving audit  : '$output_file'"
        create_dir_audit "$dirname" "$output_file"
        echo "retval: $retval"
        echo "retval1: $retval1"
        if [ $retval1 -ne 0 ]; then
            echo "ERROR: create_dir_audit ran into an error within create_dir_audit -- bailing"
            #retval1=$retval
            break
        fi
    done
    popd > /dev/null 2>&1
}

function create_backup_audits {
    local -n create_backup_audits_retval=retval
    local -n dirs=$1
    local output_dir=$2
    echo "audit dirs: ${dirs[*]}"
    echo "output dir: $output_dir"

    len=${#dirs[@]}
    for (( i=0; i<$len; i++ )); do
        create_backup_audit "${dirs[$i]}" "$output_dir" create_backup_audits_retval
        echo "retval: $retval"
        echo "retval: $create_backup_audits_retval"
        if [ $retval -ne 0 ]; then
            echo "ERROR: exiting early due to error $retval from create_backup_audit"
            exit $retval
        fi
    done
}

function usage {
    if [ -n "$1" ]; then
        echo "$1" >&2
    fi
    echo "usage: create_backup_audit.sh [-h | --help] | [-v | --verbose] [-o OUTPUT_DIR] AUDIT_DIR [AUDIT_DIR...]"
    echo
    echo "Using hashdeep create an audit file"
    echo
    echo "positional arguments:"
    echo "  {AUDIT_DIR}                         : One or more directories to run an audit"
    echo
    echo "optional arguments:"
    echo "  -v            | --verbose           : Output additional debugging information"
    echo "  -o OUTPUT_DIR | --output OUTPUT_DIR : The directory to save audit files"
    echo
    echo "examples:"
    echo "  create_backup_audit.sh '/Volumes/Seagate Backup/old-backups'"
    echo "    This will create a '/tmp/backup_<dir>.txt' file for eaach subdirectory"
    echo "    in '/Volumes/Seagate Backup/old-backups'"
    echo "  create_backup_audit.sh -o '$HOME/' '/Volumes/Seagate Backup/old-backups'"
    echo "    This will create a '$HOME/hash-<dir-lower-case-space-replaced-with-dash>.txt' file for eaach subdirectory"
    echo "    in '/Volumes/Seagate Backup/old-backups'"
}

options=$(getopt --o o:hv --long output:,help,verbose -n "$0" -- "$@")

if [ $? != 0 ]; then
    echo "ERROR: failed to parse options... exiting." >&2
    exit 2
fi

eval set -- "$options"
unset options

audit_dirs=()
output_dir='/tmp/'
while true; do
    case "$1" in
        '-h'|'--help' )
            usage
            exit 0
            ;;
        '-v'|'--verbose' )
            VERBOSE=true
            shift
            ;;
        '-o'|'--output' )
            output_dir="$2"
            shift 2
            ;;
        '--' )
            shift
            break
            ;;
        * )
            usage "ERROR: Internal error!"
            exit 1
            ;;
    esac
done

for arg; do
    audit_dirs+=("$arg")
done

if [ ${#audit_dirs[@]} -eq 0 ]; then
    usage "ERROR: missing positional argument(s) audit directory"
    exit 1
fi

len=${#audit_dirs[@]}
for (( i=0; i<$len; i++ )); do
    if [ ! -d "${audit_dirs[$i]}" ]; then
        usage "ERROR: the audit directory '${audit_dirs[$i]}' is not a valid directory"
        exit 1
    fi
done

if [ ! -d "$output_dir" ]; then
    usage "ERROR: -o | --output parameter must specifiy a valid directory"
    exit 1
else
    [ "${output_dir: -1}" == "/" ] && output_dir="${output_dir: : -1}" || output_dir="$output_dir"
fi

create_backup_audits audit_dirs $output_dir
