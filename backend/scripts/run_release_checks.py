from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def main() -> int:
    commands = [
        ([sys.executable, "-m", "compileall", "app"], BACKEND),
        ([sys.executable, "tests/smoke_api.py"], BACKEND),
        ([sys.executable, "tests/prd_smoke_api.py"], BACKEND),
        (["npm.cmd" if sys.platform == "win32" else "npm", "run", "build"], FRONTEND),
    ]
    for command, cwd in commands:
        print(f"\n$ {' '.join(command)}  # cwd={cwd}")
        result = subprocess.run(command, cwd=cwd, check=False)
        if result.returncode != 0:
            return result.returncode
    print("\nRelease checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
