"""Audit the exact Git staging area and submission ZIP without printing secrets."""
import json
import re
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config.settings import Settings


def main() -> int:
    command = ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT)]
    names = subprocess.check_output(command + ["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"]).decode().split("\0")
    # Include already committed tracked files as well, so repeated publication audits remain complete.
    tracked = subprocess.check_output(command + ["ls-files", "-z"]).decode().split("\0")
    names = sorted(set(filter(None, names + tracked)))
    key = Settings().google_api_key.get_secret_value().encode()
    patterns = [rb"AIza[0-9A-Za-z_-]{30,}", rb"gh[pousr]_[0-9A-Za-z]{30,}"]
    failures = []

    def inspect(name: str, data: bytes) -> None:
        parts = Path(name).parts
        if any(part in {".venv", ".cache", "__pycache__", "uploads", "tmp", ".git"} for part in parts):
            failures.append(f"Excluded directory staged: {name}")
        if Path(name).name.startswith(".env") and Path(name).name != ".env.example":
            failures.append(f"Environment file staged: {name}")
        if (key and key in data) or any(re.search(pattern, data) for pattern in patterns):
            failures.append(f"Potential secret detected in: {name}")
        if len(data) > 10 * 1024 * 1024:
            failures.append(f"Unexpected large artifact: {name}")

    for name in names:
        data = subprocess.check_output(command + ["show", f":{name}"])
        inspect(name, data)
        if name.endswith(".pdf") and data != (ROOT / name).read_bytes():
            failures.append(f"Staged PDF bytes differ from verified source: {name}")
    archive_path = ROOT / "DocuMind_AI_RAG_Assignment.zip"
    archive_files = 0
    if archive_path.exists():
        with ZipFile(archive_path) as archive:
            assert archive.testzip() is None
            for name in archive.namelist():
                inspect(name, archive.read(name))
                archive_files += 1
    result = {"staged_or_tracked_files": len(names), "archive_files": archive_files,
              "checks": "configured credential bytes, common token patterns, excluded paths and oversized files",
              "passed": bool(names) and not failures, "failures": failures}
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
