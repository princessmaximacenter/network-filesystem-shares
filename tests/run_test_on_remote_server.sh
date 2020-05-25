#!/usr/bin/env bash

display_usage() {
	echo "This script will initiate tests"
	echo -e "\nUsage:\n$0 <SSH_TARGET_HOST> <SSH_TARGET_DIR> \n"
	}

set -xeu

# if less than two arguments supplied, display usage
	if [  $# -le 1 ]
	then
		display_usage
		exit 1
	fi


target_host="$1"
target_dir="$2"
this_script_path="$( cd "$(dirname "$0")" ; pwd -P )"
nfs4_share_dir=$(realpath "${this_script_path}/..")

ssh ${target_host} "chmod u+rwx -R ${target_dir}; rm -rf ${target_dir}; mkdir $target_dir" || exit 33

rsync -vvr "${nfs4_share_dir}/" "${target_host}:${target_dir}" \
  --exclude ".idea" \
  --exclude "__pycache__" \
  --exclude ".DS_Store" \
  --exclude "venv"

ssh ${target_host} "
command -v python3 >/dev/null 2>&1 || module load python/3.6.1;
cd ${target_dir};
python3 -m venv venv;
source venv/bin/activate;
python setup.py test;
"
