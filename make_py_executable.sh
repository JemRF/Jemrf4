#!/usr/bin/env bash
set -euo pipefail

# Usage: ./make_py_executable.sh [--dry-run|-n]
# Makes all .py files in the current directory and subdirectories executable.

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" || "${1:-}" == "-n" ]]; then
  DRY_RUN=true
fi

# List .py files while excluding .git and __pycache__ directories
list_files() {
  find . -type f -name "*.py" ! -path "./.git/*" ! -path "*/__pycache__/*" -print0
}

if $DRY_RUN; then
  echo "Dry run: files that would be made executable:"
  list_files | xargs -0 -n1 echo
  exit 0
fi

# Apply chmod +x to each file (safe for spaces/newlines in filenames)
list_files | while IFS= read -r -d '' file; do
  if chmod +x "$file"; then
    printf "Made executable: %s\n" "$file"
  else
    printf "Failed: %s\n" "$file" >&2
  fi
done
