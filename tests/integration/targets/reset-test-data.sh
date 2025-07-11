#!/usr/bin/env bash

#set -eux

#source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs

#pip install -r requirements.txt

echo "PWD=${PWD}"

PROJECT_DIR="$( git rev-parse --show-toplevel )"
WORKDIR="${PROJECT_DIR}/.."

#VAULTPASS_FILEPATH='.vault_pass'
VAULTPASS_FILEPATH="${PROJECT_DIR}/.vault_pass"

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
SCRIPT_FILE="$(basename "$0")"
PLAYBOOK="${SCRIPT_FILE%.*}.yml"

echo "SCRIPT_DIR=[${SCRIPT_DIR}]"
echo "SCRIPT_FILE=[${SCRIPT_FILE}]"
echo "PLAYBOOK=[${PLAYBOOK}]"
echo "PROJECT_DIR=${PROJECT_DIR}"

#export ANSIBLE_ROLES_PATH=./
#export ANSIBLE_COLLECTIONS_PATH=${PROJECT_DIR}/collections
export ANSIBLE_COLLECTIONS_PATH=${PROJECT_DIR}/collections:${WORKDIR}/requirements_collections
##export ANSIBLE_DEBUG=1
export ANSIBLE_KEEP_REMOTE_FILES=1
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

rm -f ./ansible.log

#execCmd="ansible-playbook $@ -e @integration_config.vault.yml --vault-password-file ${VAULTPASS_FILEPATH} ${PLAYBOOK}"
execCmd="ansible-playbook ${*} --vault-password-file ${VAULTPASS_FILEPATH} ${PLAYBOOK}"

echo "execCmd=${execCmd}"
${execCmd}
