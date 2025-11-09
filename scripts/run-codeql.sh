#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DB_DIR="${REPO_ROOT}/temp/codeql-db"
SARIF_PATH="${REPO_ROOT}/temp/codeql.sarif"
CSV_PATH="${REPO_ROOT}/temp/codeql-findings.csv"

echo "[codeql] Preparing database directory at ${DB_DIR}"
rm -rf "${DB_DIR}"
mkdir -p "${REPO_ROOT}/temp"

echo "[codeql] Creating database from ${REPO_ROOT}/backend"
codeql database create "${DB_DIR}" \
  --language=python \
  --source-root="${REPO_ROOT}/backend"

echo "[codeql] Ensuring query packs are available"
codeql pack download codeql/python-queries

echo "[codeql] Analyzing database with standard Python security suite"
codeql database analyze "${DB_DIR}" \
  codeql/python-queries:codeql-suites/python-code-scanning.qls \
  --format=sarifv2.1.0 \
  --output="${SARIF_PATH}"

echo "[codeql] Results written to ${SARIF_PATH}"

echo "[codeql] Exporting findings to ${CSV_PATH}"
codeql database interpret-results "${DB_DIR}" \
  --format=csv \
  --output="${CSV_PATH}"

echo "[codeql] CSV results written to ${CSV_PATH}"
