#!/usr/bin/env bash

display_help()
{
   # Display Help
   echo "Run python cProfile module on a script"
   echo " python -m cProfile -s <field> example.py"
   echo
   echo "Syntax: cprofile.sh "
   echo "Syntax: cprofile.sh  [-s] <python-script.py>"
   echo "options:"
   echo "-s    sort by the keys found in sort_stats:"
   echo "       calls (call count)"
   echo "       cumulative (cumulative time)"
   echo "       cumtime (cumulative time)"
   echo "       file (file name)"
   echo "       filename (file name)"
   echo "       module (file name)"
   echo "       ncalls (call count)"
   echo "       pcalls (primitive call count)"
   echo "       line (line number)"
   echo "       name (function name)"
   echo "       nfl (name/file/line)"
   echo "       stdname (standard name)"
   echo "       time (internal time)"
   echo "       tottime (internal time)"
   echo "-h    Print this Help."
   echo "-v    Verbose mode."
   echo
}

sort_arg="tottime"

while getopts "hs:" option; do
    case $option in
        h )
            display_help
            exit;;
        s )
            sort_arg=$OPTARG
            ;;
        \? )
            echo "Invalid option: $OPTARG" 1>&2
            exit;;
        : )
            echo "Invalid option: $OPTARG requires an argument" 1>&2
            exit;;
    esac
done
shift $((OPTIND -1))

script_name=$@

if [ -z "${sort_arg}" ]; then
    echo "Invalid sort arg"
    display_help
    exit
elif [ -z "${script_name}" ]; then
    echo "No script specified"
    display_help
    exit
fi

echo "python3 -m cProfile -s ${sort_arg} ${script_name}"
python3 -m cProfile -s ${sort_arg} ${script_name}

