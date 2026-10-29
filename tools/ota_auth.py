# PlatformIO-Skript für env:ota: OTA-Passwort aus src/secrets.h übernehmen,
# damit es nur an einer Stelle steht (secrets.h ist nicht eingecheckt).
import re
from pathlib import Path

Import("env")  # noqa: F821

secrets = Path(env.subst("$PROJECT_SRC_DIR")) / "secrets.h"  # noqa: F821
m = re.search(r'#define\s+SECRET_OTA_PASS\s+"([^"]*)"', secrets.read_text()) if secrets.exists() else None
if m:
    env.Append(UPLOAD_FLAGS=[f"--auth={m.group(1)}"])  # noqa: F821
else:
    print("ota_auth.py: kein SECRET_OTA_PASS in src/secrets.h – ESP erwartet dann das AP-Passwort")
