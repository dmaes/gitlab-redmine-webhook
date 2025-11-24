#! /bin/bash

set -eo pipefail

helm package helm-chart
echo "${HELM_PASSWORD}" | helm registry login ghcr.io -u "${HELM_USERNAME}" --password-stdin
helm push \
  "gitlab-redmine-webhook-${VERSION}.tgz" \
  "oci://ghcr.io/${GITHUB_REPOSITORY_OWNER}/helm"
