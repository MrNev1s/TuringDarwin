#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIGURATION="${1:-Debug}"
OUTPUT="$ROOT/build/$CONFIGURATION"
LOG="$ROOT/build/build-${CONFIGURATION}.log"
MANIFEST="$ROOT/build/build-${CONFIGURATION}.manifest.txt"

[[ "$(uname -s)" == "Darwin" ]] || { echo "Build must run on macOS." >&2; exit 2; }
XCODE_VERSION="$(xcodebuild -version | sed -n '1s/^Xcode //p')"
SDK_VERSION="$(xcrun --sdk macosx --show-sdk-version)"
[[ "$XCODE_VERSION" == "16.2" ]] || { echo "Required Xcode 16.2; found $XCODE_VERSION" >&2; exit 2; }
[[ "$SDK_VERSION" == "15.2" ]] || { echo "Required macOS SDK 15.2; found $SDK_VERSION" >&2; exit 2; }
[[ -d "$ROOT/MacKernelSDK/Headers" ]] || { echo "Run tools/bootstrap-sdk.sh first." >&2; exit 2; }
[[ -f "$ROOT/MacKernelSDK.lock" ]] || { echo "Missing MacKernelSDK.lock." >&2; exit 2; }

python3 "$ROOT/tools/safety-audit.py"
mkdir -p "$OUTPUT"

{
  echo "date_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "sw_vers=$(sw_vers -productVersion)"
  echo "build_version=$(sw_vers -buildVersion)"
  echo "xcode=$(xcodebuild -version | tr '\n' ';')"
  echo "sdk_path=$(xcrun --sdk macosx --show-sdk-path)"
  echo "sdk_version=$(xcrun --sdk macosx --show-sdk-version)"
  echo "sdk_commit=$(git -C "$ROOT/MacKernelSDK" rev-parse HEAD)"
  echo "source_commit=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo uncommitted-source-tree)"
} > "$MANIFEST"

set -o pipefail
xcodebuild \
  -project "$ROOT/TuringProbe.xcodeproj" \
  -target TuringProbe \
  -configuration "$CONFIGURATION" \
  ARCHS=x86_64 ONLY_ACTIVE_ARCH=YES \
  CONFIGURATION_BUILD_DIR="$OUTPUT" \
  clean build | tee "$LOG"

KEXT="$OUTPUT/TuringProbe.kext"
[[ -d "$KEXT" ]] || { echo "Expected output missing: $KEXT" >&2; exit 4; }
plutil -lint "$KEXT/Contents/Info.plist"
kextutil -n "$KEXT" 2>&1 | tee "$ROOT/build/kextutil-${CONFIGURATION}.txt" || true
/usr/bin/codesign -dv --verbose=4 "$KEXT" > "$ROOT/build/codesign-${CONFIGURATION}.txt" 2>&1 || true
shasum -a 256 "$KEXT/Contents/MacOS/TuringProbe" >> "$MANIFEST"
echo "Built: $KEXT"
