#!/bin/bash
# 구조 검증 스크립트: 파일 크기, eval, print 자동 검출
# 의존성 없음 (POSIX find + grep + awk)
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

status=0

# 검사 대상 Python 파일 목록 (캐시/데이터 제외)
py_files() {
  find . -type f -name '*.py' \
    -not -path '*/__pycache__/*' \
    -not -path '*/data/*' \
    -not -path '*/.venv/*' \
    -not -path '*/venv/*'
}

echo "[check-structure] oversize python files (>300 lines)"
oversized="$(py_files | while read -r f; do
  lines=$(wc -l < "$f" | tr -d ' ')
  if [ "$lines" -gt 300 ]; then
    printf '  %6d %s\n' "$lines" "$f"
  fi
done)"
if [ -n "${oversized}" ]; then
  echo "${oversized}"
  status=1
else
  echo "  OK"
fi

echo
echo "[check-structure] eval() usage (core code only)"
eval_hits="$(py_files \
  | grep -v '/backtest/' \
  | grep -v '/graph/' \
  | grep -v '/crawl/' \
  | xargs grep -Hn 'eval(' 2>/dev/null || true)"
if [ -n "${eval_hits}" ]; then
  echo "${eval_hits}"
  status=1
else
  echo "  OK"
fi

echo
echo "[check-structure] print() usage (core code only)"
# 제외: backtest/graph/crawl (도구), bin/ (CLI 스크립트는 stdout 전제)
print_hits="$(py_files \
  | grep -v '/backtest/' \
  | grep -v '/graph/' \
  | grep -v '/crawl/' \
  | grep -v '/bin/' \
  | xargs grep -Hn '^[[:space:]]*print(' 2>/dev/null || true)"
if [ -n "${print_hits}" ]; then
  echo "${print_hits}"
  status=1
else
  echo "  OK"
fi

echo
echo "[check-structure] hardcoded secrets (token/api_key/secret_key literals)"
secret_hits="$(py_files \
  | xargs grep -HnE "(TOKEN|API_KEY|SECRET_KEY|ACCESS_KEY)[[:space:]]*=[[:space:]]*['\"][0-9A-Za-z][0-9A-Za-z_\-]{10,}['\"]" 2>/dev/null || true)"
if [ -n "${secret_hits}" ]; then
  echo "${secret_hits}"
  status=1
else
  echo "  OK"
fi

echo
if [ "$status" -eq 0 ]; then
  echo "[check-structure] PASS"
else
  echo "[check-structure] FAIL"
fi
exit "${status}"
