"""
Vital AI — convenience launcher.

Usage:
    python main.py             # start the server
    python main.py --help      # show options

Or run directly from vital-care-backend/:
    uvicorn app.main:app --reload
"""
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).parent / "vital-care-backend"


def main():
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    host  = next((a.split("=")[1] for a in args if a.startswith("--host=")), "127.0.0.1")
    port  = next((a.split("=")[1] for a in args if a.startswith("--port=")), "8000")
    reload = "--no-reload" not in args

    cmd = [
        sys.executable, "-m", "uvicorn", "app.main:app",
        f"--host={host}", f"--port={port}",
    ]
    if reload:
        cmd.append("--reload")

    print(f"\n🚀  Vital AI starting at http://{host}:{port}\n")
    subprocess.run(cmd, cwd=BACKEND)


if __name__ == "__main__":
    main()
