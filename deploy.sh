#!/bin/sh

set -e
set -x

HOST="root@176.58.117.254"
DEPLOY_TO="src/lift-me-up"

ssh "${HOST}" mkdir -p "${DEPLOY_TO}"
git ls-files -z | rsync -avz0 --files-from=- -e ssh . "${HOST}":"${DEPLOY_TO}/"

if ! ssh "${HOST}" test -x "${DEPLOY_TO}/.venv/bin/activate"; then
  ssh "${HOST}" cd "${DEPLOY_TO}" '&&' pyvenv .venv
fi
ssh "${HOST}" cd "${DEPLOY_TO}" '&&' source .venv/bin/activate '&&' pip install -r requirements.txt


ssh "${HOST}" mkdir -p /etc/sv/lift-me-up
scp deploy/runit/run deploy/runit/finish "${HOST}":/etc/sv/lift-me-up/
ssh "${HOST}" chmod 755 /etc/sv/lift-me-up/run /etc/sv/lift-me-up/finish
ssh "${HOST}" ln -sf /etc/sv/lift-me-up /etc/service/lift-me-up
ssh "${HOST}" sv restart lift-me-up
