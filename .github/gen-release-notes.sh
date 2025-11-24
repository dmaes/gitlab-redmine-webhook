#!/bin/bash

# shellcheck disable=SC2129

set -eo pipefail

echo "Releasing ${CI_COMMIT_TAG}"

CHANGELOG_FILE="${CHANGELOG_FILE:-CHANGELOG.md}"
NOTES=.github/release_notes.md

grep -E "^## \[v?${VERSION}\]" "$CHANGELOG_FILE" \
  | sed -E "s/^## \[v?${VERSION}\] (.+)$/# v${VERSION} \1/g" \
  > $NOTES

echo "" >> $NOTES

if [ ! -z "$RELEASE_NOTES_PRE" ]; then
  echo "$RELEASE_NOTES_PRE" >> $NOTES
  echo "" >> $NOTES
fi

echo "## Changelog" >> $NOTES
sed -rn "/^## \[v?${VERSION}\]/,/^## \[/p" "$CHANGELOG_FILE" \
  | grep -vE '^## \[' >> $NOTES

cat $NOTES
