#!/usr/bin/env bash

#set -eux

#source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs

#pip install -r requirements.txt

#echo "==> ENV"
#echo "$(export -p | sed 's/declare -x //')"

#VERSION="2025.7.1"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="$(basename "$0")"
SCRIPT_NAME_PREFIX="${SCRIPT_NAME%.*}"

PLAYBOOK="${SCRIPT_NAME_PREFIX}.yml"
REPO_DIR="$(cd "$SCRIPT_DIR/" && git rev-parse --show-toplevel)"

## only needed if sourcing local private collections by source instead of galaxy
## NEEDED when there is are updates/changes to the dependent collections
## to be deployed along with the project repo update(s)
#REPO_PARENT_DIR="${REPO_DIR}/.."
REPO_PARENT_DIR="$(dirname "${REPO_DIR}")"

VAULTPASS_FILEPATH="${HOME}/.vault_pass"
if [[ -f "${REPO_DIR}/.vault_pass" ]]; then
  VAULTPASS_FILEPATH="${REPO_DIR}/.vault_pass"
fi
#VAULT_FILEPATH="./../integration_config.vault.yml"
#TEST_VARS_FILE="test-vars.yml"

_INSTALL_GALAXY_COLLECTIONS="${INSTALL_GALAXY_COLLECTIONS:-0}"
_UPGRADE_GALAXY_COLLECTIONS="${UPGRADE_GALAXY_COLLECTIONS:-0}"
_FORCE_GALAXY_COLLECTIONS="${FORCE_GALAXY_COLLECTIONS:-0}"

USE_SOURCE_COLLECTIONS=0
SOURCE_COLLECTIONS_PATH="${REPO_PARENT_DIR}/requirements_collections"

echo "SCRIPT_DIR=[${SCRIPT_DIR}]"
echo "SCRIPT_NAME=[${SCRIPT_NAME}]"
echo "PLAYBOOK=[${PLAYBOOK}]"
echo "REPO_PARENT_DIR=${REPO_PARENT_DIR}"
echo "REPO_DIR=${REPO_DIR}"

#echo "VAULT_FILEPATH=${VAULT_FILEPATH}"
#echo "VAULT_ID=${VAULT_ID}"

ANSIBLE_COLLECTION_REQUIREMENTS="${REPO_DIR}/collections/requirements.yml"
#ANSIBLE_COLLECTION_REQUIREMENTS="${REPO_DIR}/collections/requirements.test.yml"

export LOCAL_COLLECTIONS_PATH="${HOME}/.ansible/collections"
#export LOCAL_COLLECTIONS_PATH="${REPO_DIR}/.ansible/collections"
#export LOCAL_COLLECTIONS_PATH="${HOME}/.ansible"
#export ANSIBLE_ROLES_PATH=./
#export ANSIBLE_COLLECTIONS_PATH="${LOCAL_COLLECTIONS_PATH}:${REPO_DIR}/collections:${REPO_PARENT_DIR}/requirements_collections"
#export ANSIBLE_COLLECTIONS_PATH="${REPO_DIR}/collections:${REPO_PARENT_DIR}/requirements_collections"
#export ANSIBLE_COLLECTIONS_PATH="${REPO_PARENT_DIR}/requirements_collections"
#export ANSIBLE_COLLECTIONS_PATH="${REPO_DIR}/collections"
export ANSIBLE_COLLECTIONS_PATH="${REPO_DIR}/collections:${LOCAL_COLLECTIONS_PATH}"
export ANSIBLE_LOG_PATH="./ansible.log"

if [[ "${USE_SOURCE_COLLECTIONS}" -eq 1 ]]; then
  export ANSIBLE_COLLECTIONS_PATH="${SOURCE_COLLECTIONS_PATH}:${ANSIBLE_COLLECTIONS_PATH}"
fi

#export ANSIBLE_DEBUG=1
export ANSIBLE_KEEP_REMOTE_FILES=1
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

## ref: https://github.com/ansible/ansible/issues/79557#issuecomment-1344168449
#export ANSIBLE_GALAXY_IGNORE=true
#export GALAXY_IGNORE_CERTS=true

cleanup_tmpdir() {
  test "${KEEP_TEMP_DIR:-0}" = 1 || rm -rf "${TEMP_DIR:-}"
}

# Install Galaxy collections if needed
function install_galaxy_collections() {
  echo "==> ansible-galaxy --version"
  ansible-galaxy --version

  ## ref: https://github.com/ansible/ansible/issues/79557#issuecomment-1344168449
  echo "==> Install Galaxy collection requirements"
#  GALAXY_INSTALL_CMD=("env ANSIBLE_GALAXY_IGNORE=true")
#  GALAXY_INSTALL_CMD+=("env GALAXY_IGNORE_CERTS=true")
#  GALAXY_INSTALL_CMD=("ansible-galaxy" "collection" "install")
#  GALAXY_INSTALL_CMD+=("--ignore-certs")
#  GALAXY_INSTALL_CMD+=("--force")

  GALAXY_INSTALL_CMD=("ansible-galaxy" "collection" "install")
  if [[ "${_FORCE_GALAXY_COLLECTIONS}" -eq 1 ]]; then
      GALAXY_INSTALL_CMD+=("--force")
  fi

  if [[ "${_UPGRADE_GALAXY_COLLECTIONS}" -eq 1 ]]; then
    GALAXY_INSTALL_CMD+=("--upgrade")
    GALAXY_INSTALL_CMD+=("--clear-response-cache")
  fi
  GALAXY_INSTALL_CMD+=("-r" "${ANSIBLE_COLLECTION_REQUIREMENTS}")
  GALAXY_INSTALL_CMD+=("-p" "${LOCAL_COLLECTIONS_PATH}")

  echo "==> ${GALAXY_INSTALL_CMD[*]}"
  if ! eval "${GALAXY_INSTALL_CMD[*]} > /dev/null"; then
    echo "Error: Failed to install Galaxy collections"
    exit 1
  fi
}

function setup_collection_test_dir() {
  local collection_namespace
  local collection_name
  local collection_source_dir

  collection_namespace=$(yq -r '.namespace' "${REPO_DIR}/galaxy.yml")
  collection_name=$(yq -r '.name' "${REPO_DIR}/galaxy.yml")

  ## ref: https://www.pixelstech.net/article/1577768087-Create-temp-file-in-Bash-using-mktemp-and-trap
  ## ref: https://stackoverflow.com/questions/4632028/how-to-create-a-temporary-directory
  mkdir -p "${HOME}/tmp"
  TEMP_DIR=$(mktemp -d -p "${HOME}/tmp" "${SCRIPT_NAME_PREFIX}_XXXXXX")

  trap cleanup_tmpdir INT TERM EXIT

  collection_source_dir="${TEMP_DIR}/ansible_collections/${collection_namespace}/${collection_name}"
  echo "COLLECTION_SOURCE_DIR=${collection_source_dir}" >&2

  mkdir -p "$(dirname "${collection_source_dir}")"
  ln -s "${REPO_DIR}" "${collection_source_dir}"

  # "Return" the directory path by printing it to stdout
  echo "${TEMP_DIR}"
}

function main() {

  PLAYBOOK_ARGS=()
  if [ $# -gt 0 ]; then
    PLAYBOOK_ARGS=("$@")
  fi

  rm -f "$ANSIBLE_LOG_PATH"

  # Set SSL certificate paths for Python
  CERT_PATH=$(python3 -m certifi 2>/dev/null || echo "")
  if [ -n "$CERT_PATH" ]; then
    export SSL_CERT_FILE=${CERT_PATH}
    export REQUESTS_CA_BUNDLE=${CERT_PATH}
  else
    echo "==> Warning: certifi module not found, SSL_CERT_FILE not set"
  fi

  if [[ "${_INSTALL_GALAXY_COLLECTIONS}" -eq 1 || "${_UPGRADE_GALAXY_COLLECTIONS}" -eq 1 ]]; then
    install_galaxy_collections
  fi

  # Call the setup function and capture the returned test directory path
  COLLECTION_BASE_DIR=$(setup_collection_test_dir)

  export ANSIBLE_COLLECTIONS_PATH="${COLLECTION_BASE_DIR}:${ANSIBLE_COLLECTIONS_PATH}"
  echo "==> ANSIBLE_COLLECTIONS_PATH=${ANSIBLE_COLLECTIONS_PATH}"

  echo "==> ansible-galaxy collection list"
  ansible-galaxy collection list

  echo "==> ansible --version"
  ansible --version

  echo "==> Playbook arguments: ${PLAYBOOK_ARGS[*]}"
  PLAYBOOK_CMD=("ansible-playbook")
#  PLAYBOOK_CMD+=("-e" "@${TEST_VARS_FILE}")
#  PLAYBOOK_CMD+=("-e" "@${VAULT_FILEPATH}")
#  PLAYBOOK_CMD+=("--vault-id" "${VAULT_ID}@${VAULTPASS_FILEPATH}")
  PLAYBOOK_CMD+=("--vault-password-file" "${VAULTPASS_FILEPATH}")
  if [[ "${#PLAYBOOK_ARGS[@]}" -gt 0 ]]; then
    PLAYBOOK_CMD+=("${PLAYBOOK_ARGS[*]}")
  fi
  PLAYBOOK_CMD+=("${PLAYBOOK}")

  echo "==> ${PLAYBOOK_CMD[*]}"
  if ! eval "${PLAYBOOK_CMD[*]}"; then
    echo "Error: Ansible playbook execution failed"
    exit 1
  fi
}

main "$@"
