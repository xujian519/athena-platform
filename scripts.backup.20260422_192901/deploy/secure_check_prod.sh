#!/bin/bash
set -e
LOG="logs/deploy/security_check_$(date +%Y%m%d%H%M%S).log"
mkdir -p logs/deploy
exec > >(tee -a "$LOG") 2>&1
echo "=== Security Check Start: $(date) ==="
echo "(1/4) SSH key presence"
for t in rsa ed25519 ecdsa; do
  if [ -f "$HOME/.ssh/id_$t" ] || [ -f "$HOME/.ssh/id_$t.pub" ]; then
    echo "FOUND: id_$t"
  else
    echo "MISSING: id_$t"
  fi
done
echo "(2/4) SSH directory permissions"
if [ -d "$HOME/.ssh" ]; then
  ls -ld "$HOME/.ssh"
else
  echo "SSH_DIR_MISSING"
fi
echo "(3/4) SSH connectivity to production hosts"
HOSTS_FILE="configs/production/hosts.txt"
if [ -f "$HOSTS_FILE" ]; then
  while read host; do
    if ssh -o BatchMode=yes -o ConnectTimeout=5 "$host" 'echo SSH_OK' 2>&1 | grep -q SSH_OK; then
      echo "SSH_OK:$host"
    else
      echo "SSH_FAIL:$host"
    fi
  done < "$HOSTS_FILE"
else
  echo "HOSTS_FILE_NOT_FOUND"
fi
echo "(4/4) Production environment config integrity"
if ls configs/production/*.yaml 1> /dev/null 2>&1; then
  echo "PROD_CONFIG_YAML_FOUND"
else
  echo "PROD_CONFIG_YAML_MISSING"
fi
echo "=== Security Check End: $(date) ==="
exit 0
