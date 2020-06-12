#!/usr/bin/env bash

display_usage() {
	echo "This script will initiate tests"
	echo -e "\nUsage:\n$0 <SSH_TARGET_HOST> <SSH_TARGET_DIR> <NFS4_MOUNT_DIR> <PYTEST ARGUMENTS>\n"
	}

set -xeu

# if less than two arguments supplied, display usage
	if [  $# -le 2 ]
	then
		display_usage
		exit 1
	fi


target_host="$1"
target_dir="$2"
nfs4_mount_dir="$3"


this_script_path="$( cd "$(dirname "$0")" ; pwd -P )"
nfs4_share_dir=$(realpath "${this_script_path}/..")

rsync -vr --filter=':- .gitignore' --exclude=.git "${nfs4_share_dir}/" "${target_host}:${target_dir}"


ssh ${target_host} "
command -v python3 >/dev/null 2>&1 || module load python/3.6.1;
cd ${target_dir};
python3 -m venv venv;
source venv/bin/activate;
pip install --ignore-installed '.[test]';
source venv/bin/activate;
pytest --basetemp=${nfs4_mount_dir} ${@:4};
"
