"""Verify that the keyboard config is present and show its expected layout.

The build cannot run without `build.yaml` and `config/west.yml`. The script is
meant to run on the host (before Docker) and is also reused by `scripts/build.py`
inside the container. It doubles as the shared message catalog for the UI
language selected via the `UI_LANG` environment variable (`en` by default).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ("build.yaml", "config/west.yml")

TREE = """\
├──.github/
├── boards/shields/xxx
├── build.yaml
├── config/
└── zephyr/"""

_MESSAGES = {
    "en": {
        "error": "error",
        "missing_config": (
            "❌ Keyboard config not found: {missing}\n\n"
            "Put the ZMK keyboard configuration files next to the project:\n\n"
            + TREE
        ),
        "no_pyyaml": "the ZMK container does not contain Python PyYAML",
        "cannot_parse": "cannot parse {path}: {exc}",
        "include_list": "build.yaml must contain an include list",
        "include_mapping": "build.yaml: include[{index}] must be a mapping",
        "missing_board": 'build.yaml: include[{index}] is missing required field "board"',
        "shield": "build.yaml: include[{index}] shield must be a string",
        "empty_include": "build.yaml include list is empty",
        "cmake_args": "build.yaml cmake-args must be a string or a list of strings",
        "snippet": "build.yaml snippet must be a string",
        "no_artifact_dir": "build completed without artifact directory: {path}",
        "no_artifacts": "no firmware artifacts found in {path}",
        "artifacts": "Artifacts: {uf2}, {other}",
        "image_description": "Select a compatible ZMK Docker image",
        "image_container": "container variant: build (default) or dev",
        "image_error": "error: {exc}\n       Set ZMK_IMAGE to an explicit compatible image to continue.",
        "manifest_unreadable": "cannot read ZMK app/west.yml for revision {revision}: {error}",
        "revision_mismatch": (
            "ZMK revision differs: config/west.yml pins {manifest}, "
            "but .github/workflows/build.yml uses {workflow}. Keep them in sync."
        ),
        "no_zephyr_revision": "ZMK app/west.yml does not specify a Zephyr revision",
        "no_zephyr_version": "cannot determine Zephyr major/minor version from revision {revision!r}",
    },
    "ru": {
        "error": "ошибка",
        "missing_config": (
            "❌ Конфиг клавиатуры не найден: {missing}\n\n"
            "Положите рядом с проектом файлы конфигурации ZMK:\n\n"
            + TREE
        ),
        "no_pyyaml": "в контейнере ZMK нет Python-модуля PyYAML",
        "cannot_parse": "не удалось разобрать {path}: {exc}",
        "include_list": "в build.yaml должен быть список include",
        "include_mapping": "build.yaml: include[{index}] должен быть словарём",
        "missing_board": 'build.yaml: include[{index}]: отсутствует обязательное поле "board"',
        "shield": "build.yaml: include[{index}]: поле shield должно быть строкой",
        "empty_include": "список include в build.yaml пуст",
        "cmake_args": "build.yaml cmake-args должен быть строкой или списком строк",
        "snippet": "build.yaml snippet должен быть строкой",
        "no_artifact_dir": "сборка завершилась без каталога артефактов: {path}",
        "no_artifacts": "в {path} не найдено артефактов прошивки",
        "artifacts": "Артефакты: {uf2}, {other}",
        "image_description": "Подобрать совместимый Docker-образ ZMK",
        "image_container": "вариант контейнера: build (по умолчанию) или dev",
        "image_error": "ошибка: {exc}\n       Задайте ZMK_IMAGE с явным совместимым образом, чтобы продолжить.",
        "manifest_unreadable": "не удалось прочитать ZMK app/west.yml для ревизии {revision}: {error}",
        "revision_mismatch": (
            "ревизия ZMK расходится: config/west.yml указывает {manifest}, "
            "а .github/workflows/build.yml использует {workflow}. Синхронизируйте их."
        ),
        "no_zephyr_revision": "в ZMK app/west.yml не указана ревизия Zephyr",
        "no_zephyr_version": "не удалось определить major/minor Zephyr из ревизии {revision!r}",
    },
}


def _lang() -> str:
    """Return the active UI language (only `ru` and `en` are supported)."""
    return "ru" if os.environ.get("UI_LANG") == "ru" else "en"


def t(key: str, **kwargs: object) -> str:
    """Return a localized message for key, falling back to English."""
    text = _MESSAGES[_lang()].get(key) or _MESSAGES["en"][key]
    return text.format(**kwargs) if kwargs else text


def missing(root: Path = ROOT) -> list[str]:
    """Return the required config files that are absent under root."""
    return [name for name in REQUIRED if not (root / name).is_file()]


def main() -> None:
    absent = missing()
    if absent:
        print(t("missing_config", missing=", ".join(absent)), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
