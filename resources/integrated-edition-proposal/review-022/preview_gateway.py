"""Assemble an exact, inactive private preview from two explicitly bound roots."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath


class PreviewError(RuntimeError):
    """A fail-closed preview input or output contract violation."""


FLAGS = ("source_admitted", "runtime_admitted", "pages_admitted", "publication_authorized")
ROLES = {"gateway", "companion", "integrated", "historical_reading", "notice", "source_download"}
ROW_KEYS = {"family", "source_path", "destination", "bytes", "sha256", "role"}
HEX = re.compile(r"[0-9a-f]{64}\Z")


def require(condition: bool, code: str) -> None:
    if not condition:
        raise PreviewError(code)


def absolute_path(value: str | Path, code: str) -> Path:
    raw = os.fspath(value)
    require(isinstance(raw, str) and raw.startswith("/") and "\\" not in raw, code)
    require(raw == "/" or all(part not in {"", ".", ".."} for part in raw[1:].split("/")), code)
    require(not any(ord(character) < 32 or ord(character) == 127 for character in raw), code)
    return Path(raw)


def relative_path(value: object) -> str:
    require(isinstance(value, str) and bool(value), "RELATIVE_PATH")
    require("\\" not in value and ":" not in value, "RELATIVE_PATH")
    require(not any(ord(character) < 32 or ord(character) == 127 for character in value), "RELATIVE_PATH")
    require(not value.startswith("/") and all(part not in {"", ".", ".."} for part in value.split("/")), "RELATIVE_PATH")
    # Reject Windows aliases even when assembling on Linux.
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    for part in value.split("/"):
        require(not part.endswith((" ", ".")) and part.split(".", 1)[0].upper() not in reserved, "RELATIVE_PATH")
    require(PurePosixPath(value).as_posix() == value, "RELATIVE_PATH")
    return value


def unaliased(path: Path, *, missing_tail: bool = False) -> None:
    """Check every existing ancestor, including the selected path itself."""
    chain = list(reversed(path.parents)) + [path]
    missing = False
    for current in chain:
        if missing:
            continue
        try:
            info = current.lstat()
        except FileNotFoundError:
            require(missing_tail, "MISSING_PATH")
            missing = True
            continue
        require(not stat.S_ISLNK(info.st_mode), "PATH_ALIAS")
        attributes = getattr(info, "st_file_attributes", 0)
        require(not attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400), "PATH_ALIAS")
        if current != path:
            require(stat.S_ISDIR(info.st_mode), "ANCESTOR_NOT_DIRECTORY")


def read_regular(path: Path) -> bytes:
    unaliased(path)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, "REGULAR_UNLINKED_FILE")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1, "REGULAR_UNLINKED_FILE")
        require((before.st_dev, before.st_ino) == (opened.st_dev, opened.st_ino), "INPUT_CHANGED")
        data = stream.read()
        after = os.fstat(stream.fileno())
    require((opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns), "INPUT_CHANGED")
    unaliased(path)
    final = path.lstat()
    require((final.st_dev, final.st_ino, final.st_nlink) == (opened.st_dev, opened.st_ino, 1), "INPUT_CHANGED")
    return data


def object_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise PreviewError("JSON_CONSTANT")


def load_record(path: Path, expected: str) -> dict:
    require(isinstance(expected, str) and HEX.fullmatch(expected) is not None, "RECORD_DIGEST_FORMAT")
    data = read_regular(path)
    require(hashlib.sha256(data).hexdigest() == expected, "RECORD_HASH")
    try:
        record = json.loads(data, object_pairs_hook=object_pairs, parse_constant=reject_constant)
    except (ValueError, UnicodeError) as error:
        raise PreviewError("RECORD_JSON") from error
    require(type(record) is dict and set(record) == {"schema", "status", "files", *FLAGS}, "RECORD_SCHEMA")
    require(record["schema"] == "astra-gateway-preview-1", "RECORD_SCHEMA")
    require(record["status"] == "PROPOSED_NOT_ADMITTED", "RECORD_STATUS")
    require(all(record[flag] is False for flag in FLAGS), "ADMISSION_FLAG")
    require(type(record["files"]) is list and bool(record["files"]), "EMPTY_ROSTER")
    return record


def inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def assemble(source: str | Path, retained: str | Path, record: str | Path,
             record_sha256: str, destination: str | Path) -> dict:
    """Preflight all bytes before creating a new destination; never overwrite."""
    roots = {"source": absolute_path(source, "SOURCE_ROOT"),
             "retained020": absolute_path(retained, "RETAINED_ROOT")}
    for root in roots.values():
        unaliased(root)
        require(root.is_dir(), "ROOT_NOT_DIRECTORY")
    require(not inside(roots["source"], roots["retained020"]) and
            not inside(roots["retained020"], roots["source"]), "SOURCE_ROOT_OVERLAP")
    output = absolute_path(destination, "DESTINATION_PATH")
    require(not any(inside(output, root) or inside(root, output) for root in roots.values()), "DESTINATION_OVERLAP")
    unaliased(output, missing_tail=True)
    require(not output.exists(), "DESTINATION_EXISTS")
    # Requiring an existing parent avoids silently creating unreviewed ancestors.
    unaliased(output.parent)
    require(output.parent.is_dir(), "DESTINATION_PARENT")
    record_path = absolute_path(record, "RECORD_PATH")
    specification = load_record(record_path, record_sha256)
    payloads = {}
    names = {}
    retained_count = 0
    for row in specification["files"]:
        require(type(row) is dict and set(row) == ROW_KEYS, "ROW_SCHEMA")
        require(isinstance(row["family"], str) and row["family"] in roots, "FAMILY")
        require(isinstance(row["role"], str) and row["role"] in ROLES, "ROLE")
        name = relative_path(row["destination"])
        origin = relative_path(row["source_path"])
        require(type(row["bytes"]) is int and row["bytes"] >= 0 and
                isinstance(row["sha256"], str) and HEX.fullmatch(row["sha256"]) is not None, "FILE_IDENTITY")
        folded = name.casefold()
        require(folded not in names, "DUPLICATE_DESTINATION")
        require(not any(folded.startswith(prior + "/") or prior.startswith(folded + "/") for prior in names), "DESTINATION_COLLISION")
        # Different case spellings of a shared directory are aliases on common hosts.
        components = name.split("/")
        for prior in payloads:
            previous = prior.split("/")
            for left, right in zip(components[:-1], previous[:-1]):
                if left.casefold() != right.casefold():
                    break
                require(left == right, "DIRECTORY_ALIAS")
        data = read_regular(roots[row["family"]] / origin)
        require(len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"], "SOURCE_HASH")
        names[folded] = name
        payloads[name] = data
        retained_count += row["family"] == "retained020"
    # All input validation is complete. Snapshot bytes prevent a later source edit
    # from changing what is written after preflight.
    unaliased(output, missing_tail=True)
    require(not output.exists(), "DESTINATION_EXISTS")
    output.mkdir(mode=0o700)
    for name, data in sorted(payloads.items()):
        target = output / name
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        unaliased(target.parent)
        with target.open("xb") as stream:
            stream.write(data)
    verify_output(output, payloads)
    return {"schema": "astra-gateway-preview-result-1", "status": "PROPOSED_NOT_ADMITTED",
            **{flag: False for flag in FLAGS}, "files": len(payloads),
            "retained020_files": retained_count, "record_sha256": record_sha256}


def verify_output(output: Path, payloads: dict[str, bytes]) -> None:
    expected_directories = {parent.as_posix() for name in payloads for parent in PurePosixPath(name).parents if parent.as_posix() != "."}
    files = set()
    directories = set()
    unaliased(output)
    for path in output.rglob("*"):
        unaliased(path)
        name = path.relative_to(output).as_posix()
        if path.is_dir():
            directories.add(name)
        else:
            files.add(name)
            require(name in payloads, "OUTPUT_ROSTER")
            require(read_regular(path) == payloads[name], "OUTPUT_HASH")
    require(files == set(payloads) and directories == expected_directories, "OUTPUT_ROSTER")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "retained", "record", "record-sha256", "destination"):
        parser.add_argument("--" + name, required=True)
    arguments = parser.parse_args()
    result = assemble(arguments.source, arguments.retained, arguments.record,
                      arguments.record_sha256, arguments.destination)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
