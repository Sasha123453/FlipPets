"""Fresh, exact-SHA dialog QA on emulator-5554 only; no implicit physical target."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
SERIAL = "emulator-5554"
PACKAGE = "org.flippets.app"
NAME = "pet-layout-qa.json"
REMOTE = f"/sdcard/Android/data/{PACKAGE}/files/{NAME}"
EXPECTED = 19
EXPECTED_NAMES = {
    "default_clock_exact_legacy_matrix", "open_editor", "reuse_existing_stage",
    "clockless_mode_button", "clockless_larger_rendered", "clockless_releases_digit_assets",
    "draft_keeps_saved_mode", "manual_scale_accessibility", "manual_x_accessibility",
    "manual_y_accessibility", "manual_adjustments_rendered", "draft_no_preference_writes",
    "layout_does_not_replay_scene", "cancel_restores_preview_and_parent",
    "apply_saves_selected_pet_mode", "per_mode_clock_profile_preserved",
    "automatic_reset_button", "reset_selected_mode_removes_manual_keys",
    "test_layout_preferences_restored",
}


def validate(result, binary):
    if result.get("apkSha256") != binary:
        raise AssertionError("Layout QA belongs to another APK SHA")
    rows = result.get("results", [])
    if result.get("tested") != EXPECTED or len(rows) != EXPECTED:
        raise AssertionError(f"Expected exactly {EXPECTED} layout checks")
    if result.get("failed") != 0 or result.get("skipped") != []:
        raise AssertionError("Layout QA has failures or missing/nonempty skipped list")
    if any(row.get("ok") is not True for row in rows):
        raise AssertionError("At least one layout check failed")
    if {row.get("test") for row in rows} != EXPECTED_NAMES:
        raise AssertionError("Layout QA cases are missing, duplicated, or unexpected")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", default="C:/platform-tools/adb.exe")
    parser.add_argument("--apk", type=Path, default=ROOT / "outputs/FlipPets.apk")
    parser.add_argument("--qa-dir", type=Path, default=ROOT / "work/qa-v03/device-files")
    parser.add_argument("--timeout", type=float, default=90)
    args = parser.parse_args()
    binary = hashlib.sha256(args.apk.read_bytes()).hexdigest()
    args.qa_dir.mkdir(parents=True, exist_ok=True)
    destination = args.qa_dir / NAME

    def adb(*parts, check=True, timeout=30):
        proc = subprocess.run([args.adb, "-s", SERIAL, *parts], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout)
        if check and proc.returncode:
            raise RuntimeError(proc.stdout + proc.stderr)
        return proc

    # Assert actual emulator identity before installation, deletion, or launch.
    if adb("shell", "getprop ro.kernel.qemu").stdout.strip() != "1":
        raise RuntimeError("Target is not an Android emulator")
    hardware = adb("shell", "getprop ro.hardware").stdout.strip()
    if not any(value in hardware for value in ("ranchu", "goldfish")):
        raise RuntimeError("Unexpected emulator hardware")
    print(adb("install", "--no-incremental", "-r", str(args.apk), timeout=120).stdout.strip(), flush=True)
    adb("shell", "am force-stop org.flippets.app")
    adb("shell", f"rm -f {REMOTE}")
    if adb("shell", f"test -e {REMOTE}", check=False).returncode == 0:
        raise RuntimeError("Failed to remove stale device layout QA result")
    destination.unlink(missing_ok=True)
    adb("shell", "am start --display 0 -n org.flippets.app/.MainActivity -f 0x10008000 --ez qaPetLayout true")
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        result = adb("shell", f"cat {REMOTE}", check=False)
        if result.returncode == 0:
            try:
                json.loads(result.stdout)
            except json.JSONDecodeError:
                pass  # Atomic write may not yet have completed.
            else:
                adb("pull", REMOTE, str(destination))
                report = json.loads(destination.read_text(encoding="utf-8"))
                validate(report, binary)
                if hashlib.sha256(args.apk.read_bytes()).hexdigest() != binary:
                    raise AssertionError("Host APK changed during layout QA")
                print(f"{EXPECTED} current APK layout checks passed: {binary}", flush=True)
                return
        time.sleep(1)
    raise TimeoutError(f"No fresh completed layout report within {args.timeout:g}s")


if __name__ == "__main__":
    main()
