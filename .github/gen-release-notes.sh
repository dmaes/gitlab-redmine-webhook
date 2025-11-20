#!/bin/bash

echo "Releasing ${CI_COMMIT_TAG}"

CHANGELOG_FILE=CHANGELOG.md

echo $GITHUB_REF

VERSION="$(echo "$GITHUB_REF" | sed -E 's/^tags\/v//')"

grep -E "^## \[v?${VERSION}\]" "$CHANGELOG_FILE" \
  | sed -E "s/^## \[v?${VERSION}\] (.+)$/# v${VERSION} \1/g" \
  > release_notes.md

echo "## Changelog" >> release_notes.md
sed -rn "/^## \[v?${VERSION}\]/,/^## \[/p" "$CHANGELOG_FILE" \
  | grep -vE '^## \[' >> release_notes.md;

cat release_notes.md
