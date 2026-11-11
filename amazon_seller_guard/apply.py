"""Restore only the known seller additions after an Amazon integration update."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile
import os

HERE = Path(__file__).resolve().parent


def replace(path, content):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    try:
        if path.exists():
            shutil.copymode(path, temporary)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def apply(base):
    rules = json.loads((HERE / "rules.json").read_text(encoding="utf-8"))
    manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    changes = {}
    for name, replacements in rules.items():
        path = base / name
        original = path.read_text(encoding="utf-8")
        updated = original
        for before, after in replacements:
            if updated.count(after) == 1:
                continue
            if updated.count(before) != 1:
                raise ValueError(f"Amazon {version}: unexpected code in {name}")
            updated = updated.replace(before, after, 1)
        compile(updated, str(path), "exec")
        if updated != original:
            changes[path] = updated.encode("utf-8")
    parser = base / "account/order_sellers.py"
    parser_bytes = (HERE / parser.name).read_bytes()
    compile(parser_bytes, str(parser), "exec")
    if parser.exists() and parser.read_bytes() != parser_bytes:
        raise ValueError(f"Amazon {version}: an existing seller parser differs")
    if not parser.exists():
        changes = {parser: parser_bytes, **changes}
    if not changes:
        return "unchanged"
    backup = HERE / "backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    originals = {}
    for path in changes:
        originals[path] = path.read_bytes() if path.exists() else None
        if originals[path] is not None:
            target = backup / path.relative_to(base)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(originals[path])
    written = []
    try:
        for path, content in changes.items():
            replace(path, content)
            written.append(path)
    except OSError:
        for path in reversed(written):
            if originals[path] is None:
                path.unlink()
            else:
                replace(path, originals[path])
        raise
    return "applied"


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("integration", type=Path)
    try:
        print(apply(cli.parse_args().integration))
    except (ValueError, OSError, KeyError, SyntaxError) as error:
        cli.exit(1, f"{error}\n")
