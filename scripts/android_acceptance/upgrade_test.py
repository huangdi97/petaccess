"""Upgrade drill: official v0.1.0 -> current signed release (sections 88-92).

Evidence recorded to artifacts/android_acceptance/upgrade/. Only touches the
owned serial; never uninstalls anything outside this AVD.
"""

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, r"E:\AI\宠物管理")

from scripts.android_acceptance import appops  # noqa: E402
from scripts.android_acceptance.adb import wait_for_device  # noqa: E402

SERIAL = "emulator-5562"
V010 = r"E:\AI\宠物管理\artifacts\v0.1.0\PetAccess_0.1.0-android-universal.apk"
CURRENT = (
    r"C:\Users\Kaiser\.pi-desktop\scratch\"
    r"904b046b-0060-4ba0-8d43-d36da17a9ecd\current-release-signed.apk"
)
EVIDENCE = Path(r"E:\AI\宠物管理\artifacts\android_acceptance\upgrade")


def main() -> int:
    wait_for_device(SERIAL, timeout=180)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    steps: list[dict] = []

    # 1. Uninstall any current build so v0.1.0 is a clean official install.
    rc, out = appops.uninstall_apk(SERIAL)
    steps.append({"step": "uninstall_current", "rc": rc, "ok": "Success" in out})
    print("uninstall_current rc={} ok={}".format(rc, "Success" in out))

    # 2. Install official v0.1.0.
    rc, out = appops.install_apk(SERIAL, V010)
    steps.append({"step": "install_v010", "rc": rc, "ok": "Success" in out})
    print("install_v010 rc={} ok={}".format(rc, "Success" in out))

    # 3. Launch v0.1.0.
    appops.shell(SERIAL, "logcat", "-c", timeout=30)
    appops.launch(SERIAL)
    time.sleep(8)
    pid1 = appops.shell_pidof(SERIAL, appops.PACKAGE)
    resumed = appops.resumed_activity(SERIAL)
    steps.append({"step": "launch_v010", "pid": pid1, "resumed": resumed[:110]})
    print(f"launch_v010 pid={pid1} resumed={resumed[:110]}")

    # 4. Upgrade: adb install -r current signed release (same identity).
    rc, out = appops.install_apk(SERIAL, CURRENT, replace=True)
    ok_upgrade = "Success" in out
    steps.append({"step": "upgrade_r", "rc": rc, "ok": ok_upgrade, "tail": out.strip()[-140:]})
    print(f"upgrade_r rc={rc} ok={ok_upgrade}")

    # 5. Verify identity + launch after upgrade.
    dump = appops.package_dump(SERIAL)
    m = re.search(r"versionName=([^ ]+)", dump)
    version = m.group(1) if m else "?"
    steps.append({"step": "post_upgrade_version", "version": version})
    print(f"post_upgrade_version={version}")

    appops.shell(SERIAL, "logcat", "-c", timeout=30)
    appops.launch(SERIAL)
    time.sleep(9)
    stages = appops.boot_trace(SERIAL)
    pid2 = appops.shell_pidof(SERIAL, appops.PACKAGE)
    steps.append(
        {
            "step": "post_upgrade_launch",
            "stages": stages,
            "pid": pid2,
            "home_ready": "HOME_READY" in stages,
        }
    )
    print(
        "post_upgrade_launch stages={} home_ready={} pid={}".format(
            stages, "HOME_READY" in stages, pid2
        )
    )

    (EVIDENCE / "upgrade_drill.json").write_text(
        json.dumps(steps, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ok = all(s.get("ok", True) for s in steps)
    print("UPGRADE DRILL", "PASS" if ok else "CHECK STEPS")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
