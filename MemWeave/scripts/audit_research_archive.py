#!/usr/bin/env python3
"""Audit the committed MemWeave research archive without extracting it to disk.

Checks the archive SHA-256, ZIP CRCs, member paths, duplicate names, symlinks,
and the embedded SHA256_MANIFEST.json. Emits a machine-readable report.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

ARCHIVE = (
    Path(__file__).resolve().parents[1]
    / "results" / "artifacts" / "2026-11-26"
    / "MemWeave_Research_Artifacts.zip"
)
EXPECTED_SHA256 = "32bc3f886f569a8fe788ca62b37032fe51d44178184b432539a7b224b7575634"
EXPECTED_MEMBERS = 53
EXPECTED_MANIFEST_FILES = 52
REPORT_DIR = Path("archive-audit-output")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_entries(value: object) -> dict[str, str]:
    """Accept common JSON manifest layouts and return path -> SHA-256."""
    if isinstance(value, dict):
        for key in ("files", "artifacts", "entries"):
            if key in value:
                return manifest_entries(value[key])
        result: dict[str, str] = {}
        for name, digest in value.items():
            if isinstance(digest, str) and re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                result[str(name)] = digest.lower()
            elif isinstance(digest, dict):
                candidate = digest.get("sha256") or digest.get("SHA256") or digest.get("hash")
                path = digest.get("path") or digest.get("file") or name
                if isinstance(candidate, str) and re.fullmatch(r"[0-9a-fA-F]{64}", candidate):
                    result[str(path)] = candidate.lower()
        return result
    if isinstance(value, list):
        result = {}
        for item in value:
            if not isinstance(item, dict):
                continue
            name = item.get("path") or item.get("file") or item.get("name")
            digest = item.get("sha256") or item.get("SHA256") or item.get("hash")
            if isinstance(name, str) and isinstance(digest, str) and re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                result[name] = digest.lower()
        return result
    return {}


def main() -> int:
    if not ARCHIVE.is_file():
        if os.environ.get("MEMWEAVE_ARCHIVE_OPTIONAL") == "1":
            report = {
                "status": "withdrawn_pending_sanitized_rebuild",
                "archive": str(ARCHIVE),
                "exists": False,
                "message": "No public research ZIP is currently published. The previous bundle was withdrawn because it contained cleartext benchmark dialogue and text-bearing outputs with unresolved redistribution terms.",
                "scope": "The absence of the current archive is intentional; this does not erase copies in earlier Git history.",
            }
            REPORT_DIR.mkdir(exist_ok=True)
            (REPORT_DIR / "archive_audit_report.json").write_text(
                json.dumps(report, indent=2) + "\\n", encoding="utf-8"
            )
            print(json.dumps(report, indent=2))
            print("PASS: archive is intentionally withdrawn pending a sanitized rebuild")
            return 0
        print(f"FAIL: archive not found: {ARCHIVE}")
        return 1

    raw = ARCHIVE.read_bytes()
    archive_sha = sha256_bytes(raw)
    report: dict[str, object] = {
        "archive": str(ARCHIVE),
        "size_bytes": len(raw),
        "sha256": archive_sha,
        "expected_sha256": EXPECTED_SHA256,
        "sha256_matches_notebook_record": archive_sha == EXPECTED_SHA256,
        "expected_member_count_including_manifest": EXPECTED_MEMBERS,
        "expected_manifest_file_count": EXPECTED_MANIFEST_FILES,
    }
    errors: list[str] = []
    warnings: list[str] = []

    if archive_sha != EXPECTED_SHA256:
        errors.append("archive SHA-256 differs from the value recorded by the Kaggle notebook")
    try:
        with zipfile.ZipFile(ARCHIVE) as archive:
            infos = archive.infolist()
            names = [item.filename for item in infos]
            report["member_count"] = len(infos)
            report["crc_error_member"] = archive.testzip()
            if len(infos) != EXPECTED_MEMBERS:
                errors.append(f"archive has {len(infos)} members; expected {EXPECTED_MEMBERS} including the manifest")
            if report["crc_error_member"] is not None:
                errors.append(f"ZIP CRC failure in {report['crc_error_member']}")
            if len(names) != len(set(names)):
                errors.append("duplicate ZIP member paths found")

            unsafe: list[str] = []
            executable: list[str] = []
            total_uncompressed = 0
            inventory = []
            for item in infos:
                path = PurePosixPath(item.filename)
                mode = (item.external_attr >> 16) & 0o170000
                if path.is_absolute() or ".." in path.parts or mode == stat.S_IFLNK:
                    unsafe.append(item.filename)
                if mode == stat.S_IFREG and ((item.external_attr >> 16) & 0o111):
                    executable.append(item.filename)
                total_uncompressed += item.file_size
                inventory.append({
                    "path": item.filename,
                    "size_bytes": item.file_size,
                    "compressed_size_bytes": item.compress_size,
                    "sha256": sha256_bytes(archive.read(item.filename)) if not item.is_dir() else None,
                })
            report["total_uncompressed_bytes"] = total_uncompressed
            report["unsafe_paths_or_symlinks"] = unsafe
            report["executable_members"] = executable
            report["inventory"] = inventory
            if unsafe:
                errors.append("unsafe path or symlink member found")
            if executable:
                warnings.append("archive contains executable-mode members; review before running")
            if total_uncompressed > 2_000_000_000:
                errors.append("uncompressed archive size exceeds 2 GB safety limit")

            manifest_names = [n for n in names if PurePosixPath(n).name == "SHA256_MANIFEST.json"]
            report["manifest_paths"] = manifest_names
            if not manifest_names:
                errors.append("SHA256_MANIFEST.json is missing from the archive")
                manifest = {}
            elif len(manifest_names) > 1:
                errors.append("multiple SHA256_MANIFEST.json files found")
                manifest = {}
            else:
                manifest = json.loads(archive.read(manifest_names[0]).decode("utf-8"))

            declared = manifest_entries(manifest)
            report["manifest_declared_file_count"] = len(declared)
            report["manifest_file_count_field"] = manifest.get("file_count") if isinstance(manifest, dict) else None
            if len(declared) != EXPECTED_MANIFEST_FILES:
                errors.append(f"manifest declares {len(declared)} files; expected {EXPECTED_MANIFEST_FILES}")
            if isinstance(manifest, dict) and manifest.get("file_count") != len(declared):
                errors.append("manifest file_count field disagrees with its files list")
            matched = []
            mismatched = []
            missing = []
            size_mismatched = []
            for name, expected in declared.items():
                if name not in names:
                    missing.append(name)
                    continue
                actual = sha256_bytes(archive.read(name))
                (matched if actual == expected else mismatched).append(name)
                declared_item = next((item for item in manifest.get("files", []) if isinstance(item, dict) and item.get("path") == name), None) if isinstance(manifest, dict) else None
                if declared_item and declared_item.get("size_bytes") is not None and len(archive.read(name)) != declared_item["size_bytes"]:
                    size_mismatched.append(name)
            report["manifest_matched_files"] = matched
            report["manifest_mismatched_files"] = mismatched
            report["manifest_missing_files"] = missing
            report["manifest_size_mismatched_files"] = size_mismatched
            if not declared:
                errors.append("manifest was found but no supported file/hash entries could be parsed")
            if mismatched:
                errors.append("one or more manifest SHA-256 values do not match archive contents")
            if missing:
                errors.append("one or more manifest entries are absent from the archive")
            if size_mismatched:
                errors.append("one or more manifest file sizes do not match archive contents")

    except (zipfile.BadZipFile, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"archive could not be safely parsed: {type(exc).__name__}: {exc}")

    report["errors"] = errors
    report["warnings"] = warnings
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "archive_audit_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    if errors:
        print("FAIL: research archive audit found errors")
        return 1
    print("PASS: archive structure, CRCs, and declared file hashes are consistent")
    print("Scope: integrity only; this does not certify privacy, licensing, scientific validity, or reproducibility.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
