#!/usr/bin/env python3
"""Build every target declared in build.yaml inside the ZMK workspace."""

from __future__ import annotations

import hashlib
import re
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

from check_config import missing, t


REPO = Path("/workspace/config-repo")
WORKSPACE = Path("/workspace/west-workspace")
OUTPUT = Path("/workspace/output")
OUTPUT_OTHER = OUTPUT / "other"
BUILD_CONFIG = REPO / "build.yaml"
ZMK = WORKSPACE / "zmk"
MANIFEST_REPO = WORKSPACE / "manifest"
ARTIFACT_SUFFIXES = (".uf2", ".hex", ".bin", ".elf", ".map")


def fail(message: str) -> NoReturn:
    print(f"{t('error')}: {message}", file=sys.stderr)
    raise SystemExit(1)


def destination(suffix: str) -> Path:
    return OUTPUT if suffix == ".uf2" else OUTPUT_OTHER


def run(*args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, env=env, check=True)


def load_yaml(path: Path) -> object:
    try:
        import yaml  # type: ignore
    except ImportError:
        fail(t("no_pyyaml"))
    try:
        with path.open(encoding="utf-8") as stream:
            return yaml.safe_load(stream)
    except Exception as exc:
        fail(t("cannot_parse", path=path, exc=exc))


def targets() -> list[dict]:
    data = load_yaml(BUILD_CONFIG)
    if not isinstance(data, dict) or not isinstance(data.get("include"), list):
        fail(t("include_list"))

    result = []
    for index, target in enumerate(data["include"]):
        if not isinstance(target, dict):
            fail(t("include_mapping", index=index))
        if not target.get("board"):
            fail(t("missing_board", index=index))
        shield = target.get("shield")
        if shield is not None and not isinstance(shield, str):
            fail(t("shield", index=index))
        result.append(target)
    if not result:
        fail(t("empty_include"))
    return result


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "target"


def cmake_args(target: dict) -> list[str]:
    args = [
        f"-DZMK_CONFIG={REPO / 'config'}",
        f"-DZMK_EXTRA_MODULES={REPO}",
        f"-DZephyr_DIR={WORKSPACE / 'zephyr' / 'share' / 'zephyr-package' / 'cmake'}",
    ]
    shield = target.get("shield")
    if shield:
        args.append(f"-DSHIELD={shield}")

    extra = target.get("cmake-args", target.get("cmake_args", []))
    if isinstance(extra, str):
        extra = [extra]
    if not isinstance(extra, list) or not all(isinstance(item, str) for item in extra):
        fail(t("cmake_args"))
    args.extend(extra)
    return args


def snippet_args(target: dict) -> list[str]:
    snippet = target.get("snippet", "")
    if not isinstance(snippet, str):
        fail(t("snippet"))
    return [arg for name in snippet.split() for arg in ("-S", name)]


def build_target(target: dict) -> None:
    board = str(target["board"])
    shield = target.get("shield") or ""
    artifact_name = target.get("artifact-name") or target.get("artifact_name")
    label = str(artifact_name or "-".join(part for part in (board, shield) if part))
    # An explicitly supplied artifact-name is the base name of each output
    # file, e.g. output/testname.uf2. Do not create an output directory.
    name = safe_name(label)
    build_dir = WORKSPACE / "build" / name

    # Drop stale artifacts from a previous build with the same name.
    for suffix in ARTIFACT_SUFFIXES:
        stale = destination(suffix) / f"{name}{suffix}"
        if stale.exists():
            stale.unlink()

    command = [
        "west", "build", "-p", "always", "-d", str(build_dir), "-b", board,
        *snippet_args(target), str(ZMK / "app"), "--", *cmake_args(target),
    ]
    build_env = os.environ.copy()
    build_env["ZEPHYR_BASE"] = str(WORKSPACE / "zephyr")
    run(*command, cwd=WORKSPACE, env=build_env)

    artifact_dir = build_dir / "zephyr"
    if not artifact_dir.is_dir():
        fail(t("no_artifact_dir", path=artifact_dir))
    copied = 0
    for artifact in artifact_dir.iterdir():
        # Only copy the final firmware artifacts. Intermediate files such as
        # zephyr_pre0.elf and zephyr_final.map would otherwise collide after
        # being renamed to the same output basename.
        suffix = artifact.suffix.lower()
        if artifact.is_file() and artifact.name.startswith("zmk.") and suffix in ARTIFACT_SUFFIXES:
            output_dir = destination(suffix)
            output_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(artifact, output_dir / f"{name}{suffix}")
            copied += 1
    if not copied:
        fail(t("no_artifacts", path=artifact_dir))
    print(t("artifacts", uf2=f"{OUTPUT}/{name}.uf2", other=f"{OUTPUT_OTHER}/{name}.*"))


def main() -> None:
    absent = missing(REPO)
    if absent:
        print(t("missing_config", missing=", ".join(absent)), file=sys.stderr)
        raise SystemExit(1)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    OUTPUT_OTHER.mkdir(parents=True, exist_ok=True)
    if MANIFEST_REPO.exists():
        shutil.rmtree(MANIFEST_REPO)
    shutil.copytree(REPO / "config", MANIFEST_REPO)
    initialized = (WORKSPACE / ".west" / "config").is_file()
    # Track the manifest so a changed config/west.yml (e.g. a new ZMK revision)
    # triggers west update instead of silently building the old checkout.
    stamp = WORKSPACE / ".west" / "manifest.sha256"
    digest = hashlib.sha256((MANIFEST_REPO / "west.yml").read_bytes()).hexdigest()
    manifest_changed = not stamp.is_file() or stamp.read_text().strip() != digest
    if not initialized:
        run("west", "init", "-l", str(MANIFEST_REPO))
    if not initialized or os.environ.get("ZMK_UPDATE") == "1" or manifest_changed:
        # Zephyr's optional group is kept: it holds nanopb, which ZMK Studio
        # (CONFIG_ZMK_STUDIO_RPC) selects. Disabling it broke Studio builds.
        run("west", "update", "--narrow", "--group-filter=+optional,+hal", cwd=WORKSPACE)
        stamp.write_text(digest)

    if os.environ.get("ZMK_UPDATE") == "1":
        return

    stale_zephyr = ZMK / "zephyr"
    if stale_zephyr.is_symlink():
        stale_zephyr.unlink()

    for target in targets():
        build_target(target)


if __name__ == "__main__":
    main()
