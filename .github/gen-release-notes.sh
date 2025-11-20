#!/bin/bash

set -eo pipefail

echo "Releasing ${CI_COMMIT_TAG}"

CHANGELOG_FILE=CHANGELOG.md
NOTES=.github/release_notes.md

VERSION="$(echo "$GITHUB_REF" | sed -E 's/^refs\/tags\/v//')"

grep -E "^## \[v?${VERSION}\]" "$CHANGELOG_FILE" \
  | sed -E "s/^## \[v?${VERSION}\] (.+)$/# v${VERSION} \1/g" \
  > $NOTES

echo "## Changelog" >> $NOTES
sed -rn "/^## \[v?${VERSION}\]/,/^## \[/p" "$CHANGELOG_FILE" \
  | grep -vE '^## \[' >> $NOTES

cat $NOTES
