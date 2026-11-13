"""Allowlist package: never include uploads, .env, weights, caches or environments."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
FILES = ["app.py", "requirements.txt", "requirements-lock.txt", ".env.example", ".gitignore", ".gitattributes",
         "pytest.ini", "README.md", "LICENSE", ".streamlit/config.toml", ".github/workflows/tests.yml"]
DIRECTORIES = ["config", "src", "assets", "sample_documents", "tests", "evaluation", "docs", "scripts"]
EXTENSIONS = {".py", ".md", ".json", ".csv", ".css", ".pdf", ".png", ".txt"}


def main():
    output = ROOT / "DocuMind_AI_RAG_Assignment.zip"
    candidates = [ROOT / name for name in FILES]
    for name in DIRECTORIES:
        candidates.extend(p for p in (ROOT / name).rglob("*") if p.is_file()
                          and p.suffix in EXTENSIONS and "__pycache__" not in p.parts)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path in sorted(set(candidates)):
            if path.is_file():
                archive.write(path, "DocuMind-AI/" + path.relative_to(ROOT).as_posix())
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert all(not n.endswith("/.env") and "/.venv/" not in n for n in archive.namelist())
        print(f"Created {output.name}: {len(archive.namelist())} files, {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
