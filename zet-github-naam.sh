#!/usr/bin/env bash
# Zet je GitHub-gebruikersnaam in de metadata en de README.
#
#   ./zet-github-naam.sh <jouw-github-naam>
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "gebruik: $0 <jouw-github-naam>" >&2
  exit 1
fi

grep -rl "JOUW-GITHUB-NAAM" . --exclude-dir=.git \
  | xargs sed -i "s|JOUW-GITHUB-NAAM|$1|g"

echo "Klaar. Gezet op: github.com/$1/teletekst-101"
grep -r "github.com/$1" custom_components/nos_teletekst/manifest.json
