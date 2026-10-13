"""Select the ZMK Docker image compatible with the configured ZMK revision.

ZMK Docker images are versioned by the Zephyr major/minor version they contain,
not by the ZMK release number.  For example, ZMK v0.3 uses Zephyr 3.5 and the
corresponding image is zmkfirmware/zmk-dev-arm:3.5-branch.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from check_config import t


ROOT = Path(__file__).resolve().parent.parent
WEST = ROOT / "config" / "west.yml"
WORKFLOW = ROOT / ".github" / "workflows" / "build.yml"


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def project_revision(manifest: str, project: str) -> str | None:
    # Stop the scan at the next project line, so an entry without its own
    # revision does not silently borrow the revision of a later project.
    match = re.search(
        rf"(?ms)^\s*-\s+name:\s+{project}\s*$(?:(?!^\s*-\s+name:).)*?^\s+revision:\s*([^#\s]+)",
        manifest,
    )
    return match.group(1).strip("'\"") if match else None


def workflow_revision(workflow: str) -> str | None:
    match = re.search(r"zmkfirmware/zmk/[^\s]+@([^\s\"']+)", workflow)
    return match.group(1) if match else None


def zmk_revision() -> str:
    """Read the ZMK revision from config/west.yml, checked against the workflow."""
    revision = project_revision(read(WEST), "zmk")
    workflow = workflow_revision(read(WORKFLOW))
    if revision and workflow and revision != workflow:
        raise RuntimeError(t("revision_mismatch", manifest=revision, workflow=workflow))
    return revision or workflow or "main"


def fetch_zmk_manifest(revision: str) -> str:
    revisions = [revision]
    # Release refs are tags (v0.3), not branches, so try the tag spelling first.
    if re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", revision):
        revisions = [f"v{revision}", revision]

    last_error: Exception | None = None
    for candidate in revisions:
        url = f"https://raw.githubusercontent.com/zmkfirmware/zmk/{candidate}/app/west.yml"
        request = Request(url, headers={"User-Agent": "zmk-config-builder"})
        try:
            with urlopen(request, timeout=15) as response:
                return response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
    raise RuntimeError(t("manifest_unreadable", revision=revision, error=last_error))


def zephyr_version(manifest: str) -> str:
    revision = project_revision(manifest, "zephyr")
    if revision is None:
        raise RuntimeError(t("no_zephyr_revision"))

    version = re.search(r"(?:^|[^0-9])([0-9]+\.[0-9]+)(?:\.[0-9]+)?(?:[^0-9]|$)", revision)
    if not version:
        raise RuntimeError(t("no_zephyr_version", revision=revision))
    return version.group(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=t("image_description"))
    parser.add_argument(
        "--container",
        choices=("build", "dev"),
        default="build",
        help=t("image_container"),
    )
    args = parser.parse_args()
    override = os.environ.get("ZMK_IMAGE")
    if override:
        print(override)
        return

    try:
        revision = zmk_revision()
        version = zephyr_version(fetch_zmk_manifest(revision))
        print(f"zmkfirmware/zmk-{args.container}-arm:{version}-branch")
    except RuntimeError as exc:
        print(t("image_error", exc=exc), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
