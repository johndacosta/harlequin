from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNC_SCRIPT = (
    REPO_ROOT / "questdb-loop" / "scripts" / "sync-harlequin-questdb-package.sh"
)
STAGING = REPO_ROOT / "questdb-loop" / "package" / "harlequin-questdb"


@pytest.fixture(scope="module")
def synced_staging() -> Path:
    assert SYNC_SCRIPT.is_file(), f"missing {SYNC_SCRIPT}"
    result = subprocess.run(
        ["bash", str(SYNC_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return STAGING


def test_staging_pyproject_entry_point(synced_staging: Path) -> None:
    pyproject = (synced_staging / "pyproject.toml").read_text(encoding="utf-8")
    assert 'questdb = "harlequin_questdb' in pyproject


def test_staging_license_present(synced_staging: Path) -> None:
    assert (synced_staging / "LICENSE").is_file()


def test_staging_readme_install_and_connect(synced_staging: Path) -> None:
    readme = (synced_staging / "README.md").read_text(encoding="utf-8")
    assert "pip install harlequin harlequin-questdb" in readme
    assert "harlequin --adapter questdb" in readme
    assert "8812" in readme
    assert "8.2.2" in readme


def test_staging_readme_auth_dev_only(synced_staging: Path) -> None:
    readme = (synced_staging / "README.md").read_text(encoding="utf-8")
    lowered = readme.lower()
    assert "not for production" in lowered or "development only" in lowered
    assert "--password quest" in readme
    assert "does not auto-supply" in lowered or "does **not** auto-supply" in readme


def test_staging_readme_limitations_anchor(synced_staging: Path) -> None:
    readme = (synced_staging / "README.md").read_text(encoding="utf-8")
    assert "KNOWN_LIMITATIONS" in readme or "Known limitations" in readme


def test_staged_adapter_details_package_relative_paths(synced_staging: Path) -> None:
    adapter_path = synced_staging / "src" / "harlequin_questdb" / "adapter.py"
    adapter_py = adapter_path.read_text(encoding="utf-8")
    match = re.search(
        r"ADAPTER_DETAILS\s*=\s*\((.*?)\)\s*\n\n\s*def __init__",
        adapter_py,
        re.DOTALL,
    )
    assert match is not None, "ADAPTER_DETAILS block not found"
    details = match.group(1)
    assert "questdb-loop/" not in details
    assert "docs/USER_GUIDE.md" in details
    assert "docs/KNOWN_LIMITATIONS.md" in details
    assert "tables()" in details
    assert "table_columns()" in details
    assert "functions()" in details


def test_staged_user_guide_catalog_hints(synced_staging: Path) -> None:
    user_guide = (synced_staging / "docs" / "USER_GUIDE.md").read_text(encoding="utf-8")
    lowered = user_guide.lower()
    assert "tables()" in user_guide
    assert "table_columns(" in user_guide
    assert "partitionby" in lowered or "partition by" in lowered
    assert "★" in user_guide or "designated" in lowered
    assert "t·day" in lowered or "t·DAY" in user_guide


def test_staged_user_guide_no_questdb_loop_paths(synced_staging: Path) -> None:
    user_guide = (synced_staging / "docs" / "USER_GUIDE.md").read_text(encoding="utf-8")
    assert "questdb-loop/" not in user_guide
    assert "docker-compose.yml" in user_guide


def test_staging_publish_md_in_sdist_manifest(synced_staging: Path) -> None:
    assert (synced_staging / "PUBLISH.md").is_file()
    pyproject = (synced_staging / "pyproject.toml").read_text(encoding="utf-8")
    assert '"PUBLISH.md"' in pyproject


def test_staging_publish_md_secrets_policy(synced_staging: Path) -> None:
    publish = (synced_staging / "PUBLISH.md").read_text(encoding="utf-8")
    lowered = publish.lower()
    assert ".env" in publish
    assert "twine upload" in lowered
    assert "pip install ./dist/harlequin_questdb-" in publish
    assert "questdb-loop/" in publish
    assert "api token" in lowered or "pypirc" in lowered


def test_staging_readme_links_publish_md(synced_staging: Path) -> None:
    readme = (synced_staging / "README.md").read_text(encoding="utf-8")
    assert "PUBLISH.md" in readme
    assert "./dist/harlequin_questdb-" in readme


def test_staged_interactions_no_destructive_drop(synced_staging: Path) -> None:
    interactions = (
        synced_staging / "src" / "harlequin_questdb" / "interactions.py"
    ).read_text(encoding="utf-8")
    lowered = interactions.lower()
    assert "drop database" not in lowered
    assert "drop schema" not in lowered


def test_uv_build(synced_staging: Path) -> None:
    dist = synced_staging / "dist"
    if dist.is_dir():
        shutil.rmtree(dist)
    result = subprocess.run(
        ["uv", "build"],
        cwd=synced_staging,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_wheel_install_resolves_questdb_entry_point(
    synced_staging: Path, tmp_path: Path
) -> None:
    dist = synced_staging / "dist"
    if not dist.is_dir() or not list(dist.glob("*.whl")):
        build = subprocess.run(
            ["uv", "build"],
            cwd=synced_staging,
            capture_output=True,
            text=True,
            check=False,
        )
        assert build.returncode == 0, build.stderr or build.stdout

    wheels = sorted(dist.glob("harlequin_questdb-*.whl"))
    assert wheels, f"no wheel in {dist}"

    venv_dir = tmp_path / "wheel-smoke-venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    pip = venv_dir / "bin" / "pip"
    python = venv_dir / "bin" / "python"

    install = subprocess.run(
        [str(pip), "install", str(wheels[-1])],
        capture_output=True,
        text=True,
        check=False,
    )
    assert install.returncode == 0, install.stderr or install.stdout

    probe = subprocess.run(
        [
            str(python),
            "-c",
            "from harlequin.plugins import load_adapter_plugins; "
            "plugins = load_adapter_plugins(); "
            "assert 'questdb' in plugins; "
            "assert plugins['questdb'].__name__ == 'HarlequinQuestDbAdapter'",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert probe.returncode == 0, probe.stderr or probe.stdout
