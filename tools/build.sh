#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIGURATION="${1:-Debug}"
BUILD_ROOT="$ROOT/build"
OUTPUT="$BUILD_ROOT/$CONFIGURATION"
LOG="$BUILD_ROOT/build-${CONFIGURATION}.log"
MANIFEST="$BUILD_ROOT/build-${CONFIGURATION}.manifest.txt"

[[ "$(uname -s)" == "Darwin" ]] || { echo "Build must run on macOS." >&2; exit 2; }
XCODE_VERSION="$(xcodebuild -version | sed -n '1s/^Xcode //p')"
SDK_VERSION="$(xcrun --sdk macosx --show-sdk-version)"
[[ "$XCODE_VERSION" == "16.2" ]] || { echo "Required Xcode 16.2; found $XCODE_VERSION" >&2; exit 2; }
[[ "$SDK_VERSION" == "15.2" ]] || { echo "Required macOS SDK 15.2; found $SDK_VERSION" >&2; exit 2; }
[[ -d "$ROOT/MacKernelSDK/Headers" ]] || { echo "Run tools/bootstrap-sdk.sh first." >&2; exit 2; }
[[ -f "$ROOT/MacKernelSDK.lock" ]] || { echo "Missing MacKernelSDK.lock." >&2; exit 2; }

python3 "$ROOT/tools/safety-audit.py"
python3 "$ROOT/tools/test-decoder-contract.py"
python3 "$ROOT/tools/test-mmio-contract.py"

# Do not pass `clean build` to xcodebuild while CONFIGURATION_BUILD_DIR lives
# inside a directory created by this script. Xcode 16 refuses to delete such
# directories during its clean phase and returns exit code 65 even when the
# following build succeeds. Remove only our known generated paths ourselves.
mkdir -p "$BUILD_ROOT"
rm -rf \
  "$OUTPUT" \
  "$BUILD_ROOT/TuringProbe.build" \
  "$BUILD_ROOT/EagerLinkingTBDs" \
  "$BUILD_ROOT/ModuleCache.noindex" \
  "$BUILD_ROOT/SDKStatCaches.noindex"
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
  echo "turingprobe_version=0.5.0"
  echo "mmio_compile_gate=TURINGPROBE_ENABLE_MMIO_READ=1"
  echo "fb_compile_gate=TURINGPROBE_ENABLE_FB_READ=1"
  echo "mmio_identity_whitelist=0x000004,0x000000,0x101000"
  echo "mmio_top_inventory=64x32@0x022700..0x0227fc"
  echo "mmio_fb_inventory=1x32@0x100ce0"
  echo "mmio_modes=-tdprobe;-tdprobe+-tdmmio-read;-tdprobe+-tdmmio-read+-tdtop-read;-tdprobe+-tdmmio-read+-tdfb-read"
} > "$MANIFEST"

set -o pipefail
xcodebuild \
  -project "$ROOT/TuringProbe.xcodeproj" \
  -target TuringProbe \
  -configuration "$CONFIGURATION" \
  ARCHS=x86_64 ONLY_ACTIVE_ARCH=YES \
  CONFIGURATION_BUILD_DIR="$OUTPUT" \
  build | tee "$LOG"

KEXT="$OUTPUT/TuringProbe.kext"
[[ -d "$KEXT" ]] || { echo "Expected output missing: $KEXT" >&2; exit 4; }
[[ -f "$KEXT/Contents/MacOS/TuringProbe" ]] || { echo "Expected executable missing." >&2; exit 4; }
plutil -lint "$KEXT/Contents/Info.plist"
kextutil -n "$KEXT" 2>&1 | tee "$BUILD_ROOT/kextutil-${CONFIGURATION}.txt" || true
/usr/bin/codesign -dv --verbose=4 "$KEXT" > "$BUILD_ROOT/codesign-${CONFIGURATION}.txt" 2>&1 || true
shasum -a 256 "$KEXT/Contents/MacOS/TuringProbe" >> "$MANIFEST"
echo "Built: $KEXT"
