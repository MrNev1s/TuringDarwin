#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCK_FILE="${1:-$ROOT/MacKernelSDK.lock}"
SDK_DIR="$ROOT/MacKernelSDK"

if [[ ! -f "$LOCK_FILE" ]]; then
  echo "Missing $LOCK_FILE" >&2
  echo "Copy MacKernelSDK.lock.example to MacKernelSDK.lock and replace the zero hash." >&2
  exit 2
fi

REF="$(tr -d '[:space:]' < "$LOCK_FILE")"
if [[ ! "$REF" =~ ^[0-9a-fA-F]{40}$ ]] || [[ "$REF" =~ ^0+$ ]]; then
  echo "MacKernelSDK.lock must contain one non-zero 40-character commit hash." >&2
  exit 2
fi

if [[ ! -d "$SDK_DIR/.git" ]]; then
  git clone https://github.com/acidanthera/MacKernelSDK.git "$SDK_DIR"
fi

git -C "$SDK_DIR" fetch --tags --prune origin
git -C "$SDK_DIR" checkout --detach "$REF"
ACTUAL="$(git -C "$SDK_DIR" rev-parse HEAD)"
[[ "$ACTUAL" == "$REF" ]] || { echo "SDK checkout mismatch" >&2; exit 3; }
echo "Pinned MacKernelSDK: $ACTUAL"
