"""Create an allowlisted source bundle; never package secrets or dependency trees."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "automotive-operations-agent-submission.zip"
DIRECTORIES = {"agents","skills","knowledge","backend","frontend","database","integrations","tests","evals","demo","docs","scripts"}
ROOT_FILES = {"AGENTS.md","TASKS.md","README.md",".env.example",".gitignore",".dockerignore","docker-compose.yml","pyproject.toml","uv.lock","requirements.txt","alembic.ini"}
BLOCKED = {".git",".venv","node_modules","dist","__pycache__",".pytest_cache","test-results","playwright-report",".runtime"}


def eligible(path):
    relative = path.relative_to(ROOT)
    if path.is_symlink() or set(relative.parts)&BLOCKED:
        return False
    if path.name==".env" or (path.name.startswith(".env.") and path.name!=".env.example"):
        return False
    if path.suffix.lower() in {".db",".pyc",".pyo",".zip",".pem",".key",".tsbuildinfo"}:
        return False
    return relative.parts[0] in DIRECTORIES or relative.as_posix() in ROOT_FILES


def main():
    required = ["README.md","demo/test_output.md","evals/evaluation_report.md","docs/verification.md","frontend/package-lock.json"]
    for name in required:
        if not (ROOT/name).is_file():
            raise RuntimeError(f"Missing verified deliverable: {name}")
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and eligible(p))
    with ZipFile(DEST,"w",ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path,Path("automotive-operations-agent")/path.relative_to(ROOT))
    with ZipFile(DEST) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist())==len(files)
        assert not any(set(Path(name).parts)&BLOCKED for name in archive.namelist())
    print(f"Created {DEST} ({len(files)} files, {DEST.stat().st_size:,} bytes)")


if __name__=="__main__":
    main()

