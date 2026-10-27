"""Non-product Windows MakeAppx fixture using a REAL Godot 4.3 template export.

The source artifact is created by this same GitHub Actions run. Its digest and
run/source identity are independently checked before any packaging. This is not
a product, install/GPU test, Partner Center Identity, or Store-ready package.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from unittest.mock import patch

QA_SHA = "e84c448e48105d15d2040f87fb279835ddd0119b"
TEMPLATE_REPO = "shihuiarenjinba-png/3d-game-template"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if os.name != "nt":
        raise RuntimeError("real MakeAppx fixture requires a Windows runner")
    workspace = Path(os.environ["GITHUB_WORKSPACE"])
    source = workspace / "dist"
    qa_root = workspace / "qa-code"
    record = json.loads((source / "build-evidence.json").read_text(encoding="utf-8"))
    if (record.get("source_repository") != TEMPLATE_REPO
            or record.get("source_sha") != os.environ["GITHUB_SHA"]
            or str(record.get("workflow_run_id")) != os.environ["GITHUB_RUN_ID"]
            or record.get("godot_version") != "4.3.stable"
            or record.get("platform") != "Windows Desktop"
            or record.get("architecture") != "x86_64"
            or record.get("status") != "QA_UNSIGNED_EXPORT"
            or record.get("msix_created") is not False
            or record.get("store_identity") is not None):
        raise RuntimeError("Godot export provenance or non-product state mismatch")
    files = record.get("files")
    if (not isinstance(files, list) or len(files) != 2
            or {f.get("name") for f in files if isinstance(f, dict)}
               != {"3d-starter.exe", "3d-starter.pck"}):
        raise RuntimeError("missing or duplicated Godot EXE/PCK evidence")
    hashes = {}
    for item in files:
        name = item["name"]
        path = source / name
        claimed = item.get("sha256")
        if (not isinstance(claimed, str) or not SHA256.fullmatch(claimed)
                or type(item.get("bytes")) is not int or item["bytes"] <= 4
                or not path.is_file() or path.is_symlink()
                or path.stat().st_size != item["bytes"]
                or sha256_file(path) != claimed):
            raise RuntimeError("Godot export byte evidence mismatch: " + name)
        hashes[name] = claimed
    if (source / "3d-starter.exe").open("rb").read(2) != b"MZ":
        raise RuntimeError("real Godot EXE lacks MZ")
    if (source / "3d-starter.pck").open("rb").read(4) != b"GDPC":
        raise RuntimeError("real Godot PCK lacks GDPC")
    observed_qa_sha = subprocess.check_output(
        ["git", "-C", str(qa_root), "rev-parse", "HEAD"], text=True).strip()
    if observed_qa_sha != QA_SHA:
        raise RuntimeError("QA verifier checkout differs from pinned commit")
    sys.path.insert(0, str(qa_root))
    sys.path.insert(0, str(qa_root / "tests"))
    from makeappx_windows_fixture import MANIFEST, PNG
    from msix_artifact_verify import verify_msix

    sdk = Path(os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)")) / "Windows Kits" / "10" / "bin"
    makeappx = sorted(sdk.glob("*/x64/makeappx.exe"), reverse=True)
    if not makeappx:
        raise RuntimeError("Windows SDK MakeAppx x64 unavailable")
    out = Path(os.environ["RUNNER_TEMP"]) / "3d-real-godot-makeappx-fixture"
    stage = out / "staging"
    (stage / "Game").mkdir(parents=True, exist_ok=True)
    (stage / "Assets").mkdir(parents=True, exist_ok=True)
    (stage / "AppxManifest.xml").write_text(MANIFEST, encoding="utf-8")
    (stage / "Assets" / "Logo.png").write_bytes(PNG)
    shutil.copyfile(source / "3d-starter.exe", stage / "Game" / "game.exe")
    shutil.copyfile(source / "3d-starter.pck", stage / "Game" / "game.pck")
    expected_export = {
        "exe_path": "Game/game.exe",
        "exe_sha256": hashes["3d-starter.exe"],
        "embed_pck": False,
        "pck_path": "Game/game.pck",
        "pck_sha256": hashes["3d-starter.pck"],
    }
    package = out / "real-godot-template-fixture.msix"
    subprocess.run([str(makeappx[0]), "pack", "/d", str(stage),
                    "/p", str(package), "/o"], check=True)
    receipt = {
        "schema_version": "1.0", "source_factory": "3d-game-factory",
        "request_id": "offline-godot-template-fixture-" + record["source_sha"][:12],
        "repository_full_name": TEMPLATE_REPO, "source_sha": record["source_sha"],
        "package_sha256": sha256_file(package),
        "windows_run_id": os.environ["GITHUB_RUN_ID"],
        "runner_evidence_id": "offline-fixture-only", "windows_launch": False,
        "tests": {"executed": 0, "failed": 0, "skipped": 0, "crashes": 0},
    }
    # Override ONLY the launch receipt shape gate, not the byte/manifest guards.
    with patch("msix_artifact_verify.inspect",
               return_value={"status": "EVIDENCE_REVIEW", "errors": []}):
        good = verify_msix(receipt, package, expected_godot_export=expected_export)
    required = ("artifact_bytes_verified", "content_types_verified",
                "blockmap_verified", "payload_executables_verified",
                "godot_export_bytes_matched")
    if good["status"] != "HOLD" or not all(good[k] is True for k in required):
        raise RuntimeError("real Godot MakeAppx fixture failed: " + repr(good))
    if any(good[k] for k in ("official_identity_verified",
                              "windows_launch_verified", "signature_verified",
                              "submission_authorized", "github_provenance_verified")):
        raise RuntimeError("fixture incorrectly promoted to real product QA")

    # Repack a modified but well-formed PCK. Its BlockMap and ZIP CRC are valid;
    # only the independent original export digest should reject the substitution.
    pck = stage / "Game" / "game.pck"
    with pck.open("r+b") as stream:
        stream.seek(-1, 2)
        last = stream.read(1)
        stream.seek(-1, 2)
        stream.write(bytes([last[0] ^ 1]))
    forged = out / "tampered-pck-repacked.msix"
    subprocess.run([str(makeappx[0]), "pack", "/d", str(stage),
                    "/p", str(forged), "/o"], check=True)
    bad_receipt = dict(receipt, package_sha256=sha256_file(forged))
    with patch("msix_artifact_verify.inspect",
               return_value={"status": "EVIDENCE_REVIEW", "errors": []}):
        bad = verify_msix(bad_receipt, forged,
                          expected_godot_export=expected_export)
    if (bad["status"] != "BLOCKED"
            or not any("Godot export payload SHA-256 mismatch" in e
                       for e in bad["errors"])):
        raise RuntimeError("repacked PCK substitution not rejected: " + repr(bad))
    forged.unlink()
    evidence = {
        "kind": "REAL_GODOT_4_3_TEMPLATE_MAKEAPPX_FIXTURE_NOT_PRODUCT",
        "template_repository": TEMPLATE_REPO,
        "template_source_sha": record["source_sha"],
        "template_export_run_id": record["workflow_run_id"],
        "qa_verifier_sha": QA_SHA,
        "makeappx_path": str(makeappx[0]),
        "exe_sha256": hashes["3d-starter.exe"],
        "pck_sha256": hashes["3d-starter.pck"],
        "msix_sha256": receipt["package_sha256"],
        "msix_bytes": package.stat().st_size,
        "verification_status": good["status"],
        "verified_byte_checks": {k: good[k] for k in required},
        "repacked_tampered_pck_rejected": True,
        "official_identity": None,
        "accepted_product": None,
        "windows_install_gpu_gui_tested": False,
        "store_submission_allowed": False,
    }
    (out / "fixture-evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
