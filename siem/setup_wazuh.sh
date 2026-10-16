#!/usr/bin/env bash
# Deploy Wazuh single-node (Docker) wired to the SIL lab:
#   * lab logs (Squid, AI gateway, WAF, Kong) mounted read-only into the manager and collected as JSON
#   * siem/rules/local_rules.xml mounted as the manager's custom rules
#   * every published port bound to 127.0.0.1 only (default credentials are never reachable from the network)
# Usage: siem/setup_wazuh.sh        (safe to re-run; it reconfigures and restarts)
set -euo pipefail
WAZUH_VERSION="${WAZUH_VERSION:-v4.14.9}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WD="$HOME/wazuh-docker"
SN="$WD/single-node"

if [ ! -d "$WD" ]; then
  echo "== Cloning wazuh-docker $WAZUH_VERSION"
  git clone -q --depth 1 -b "$WAZUH_VERSION" https://github.com/wazuh/wazuh-docker.git "$WD"
fi
cd "$SN"

if [ ! -f config/wazuh_indexer_ssl_certs/root-ca.pem ]; then
  echo "== Generating the indexer TLS certificates"
  docker compose -f generate-indexer-certs.yml run --rm generator
fi

echo "== Binding published ports to localhost only"
sed -i -E 's#^(\s+- )"?(1514|1515|55000|9200):(1514|1515|55000|9200)"?$#\1"127.0.0.1:\2:\3"#' docker-compose.yml
sed -i -E 's#^(\s+- )"?514:514/udp"?$#\1"127.0.0.1:514:514/udp"#' docker-compose.yml
sed -i -E 's#^(\s+- )443:5601$#\1"127.0.0.1:443:5601"#' docker-compose.yml

echo "== Mounting the lab logs and the SIL custom rules into the manager"
if ! grep -q "/var/log/sil" docker-compose.yml; then
  sed -i "s#^\(\s*\)- ./config/wazuh_cluster/wazuh_manager.conf:/wazuh-config-mount/etc/ossec.conf#&\n\1- $REPO/lab/logs:/var/log/sil:ro\n\1- $REPO/siem/rules:/wazuh-config-mount/etc/rules:ro   # folder, not file: single-file mounts break when editors replace the file#" docker-compose.yml
fi

echo "== Adding the lab log sources to the manager configuration"
CONF=config/wazuh_cluster/wazuh_manager.conf
if ! grep -q "/var/log/sil/squid/access.json" "$CONF"; then
  { echo "<ossec_config>"; cat "$REPO/siem/ossec-localfile.xml" | sed '/^<!--/,/-->$/d'; echo "</ossec_config>"; } >> "$CONF"
fi

echo "== Checks"
grep -n "127.0.0.1:" docker-compose.yml | sed 's/^/   /'
grep -n "/var/log/sil\|siem/rules" docker-compose.yml | sed 's/^/   /'
grep -c "/var/log/sil/" "$CONF" | xargs -I{} echo "   $CONF collects {} lab log files"

echo "== Starting Wazuh (the dashboard takes 1-3 minutes to come up)"
docker compose up -d
echo
echo "Dashboard: https://localhost  (user admin / password SecretPassword - default, reachable from this machine only)"
echo "Test a rule: docker exec -it single-node-wazuh.manager-1 /var/ossec/bin/wazuh-logtest"
