#! /bin/bash

set -eo pipefail

helm package helm-chart
helm registry login ghcr.io -u "${HELM_USERNAME}" -p "${HELM_PASSWORD}"
helm push \
  "gitlab-redmine-webhook-v${VERSION}.tgz" \
  "oci://ghcr.io/${GITHUB_REPOSITORY_OWNER}/helm"
