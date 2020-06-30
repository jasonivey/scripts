#!/usr/bin/env bash

if [ $# -ne 3 ] ; then
	printf "Usage:   <server type> <number> <environment>\n"
	printf "example: pub 2 qa\n"
	exit 1
fi

# check the server type
case $1 in
	pub)
		server="dynpub-"
		;;
	pack)
		server="dynpak-"
		;;
	admin)
		server="dynadm-"
		;;
	ks)
		;& # fallthrough
	keystore)
		server="ks-"
		;;
	*)
		echo "Unknown server type: $1  {pub|pack|admin|ks}"
		exit 1
esac

# check the number
re='^[0-9]+$'
if ! [[ $2 =~ $re ]] ; then
	printf "error: Not a number '$2'\n"
	exit 1
fi
number=$2

# check the environment
case $3 in
	dev)
		prefix=""
		postfix=".dev.movenetworks.com"
		number=$(printf "%03d" $number)
		# handle special dev names, they don't follow the normal naming convention
		if [ $server == "dynadm-" ] ; then
			server="dya"
		elif [ $server == "dynpak-" ] ; then
			server="dp"
		elif [ $server == "dynpub-" ] ; then
			server="dypub"
		elif [ $server == "ks-" ] ; then
			server="ks"
		fi
		;;
	qa)
		prefix="q-slc3-"
		postfix=".q.movetv.com"
		;;
	beta)
		prefix="b-slc3-"
		postfix=".b.movetv.com"
		;;
	prod)
		prefix="p-gil1-"
		postfix=".p.movetv.com"
		;;
	*)
		echo "Unknown environment: $3  {dev|qa|beta|prod}"
		exit 1
esac

ssh administrator@$prefix$server$number$postfix
