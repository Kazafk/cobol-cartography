from pathlib import Path

import pytest

from src.indexing.scanner import FileKind, scan_workspace


def test_detects_cobol_program(tmp_path):
    (tmp_path / "PGMTEST.cbl").write_text("IDENTIFICATION DIVISION.")
    inv = scan_workspace(str(tmp_path))
    assert len(inv.programs) == 1
    assert inv.programs[0].kind == FileKind.PROGRAM


def test_detects_uppercase_extension(tmp_path):
    (tmp_path / "PGMTEST.COB").write_text("IDENTIFICATION DIVISION.")
    inv = scan_workspace(str(tmp_path))
    assert len(inv.programs) == 1


def test_detects_copybook(tmp_path):
    (tmp_path / "CPYTEST.cpy").write_text("01 WS-FIELD PIC X(10).")
    inv = scan_workspace(str(tmp_path))
    assert len(inv.copybooks) == 1
    assert inv.copybooks[0].kind == FileKind.COPYBOOK


def test_detects_jcl(tmp_path):
    (tmp_path / "JOBTEST.jcl").write_text("//JOBTEST JOB CLASS=A")
    inv = scan_workspace(str(tmp_path))
    assert len(inv.jcl_jobs) == 1
    assert inv.jcl_jobs[0].kind == FileKind.JCL


def test_ignores_unknown_extensions(tmp_path):
    (tmp_path / "README.md").write_text("readme")
    (tmp_path / "config.yaml").write_text("key: value")
    inv = scan_workspace(str(tmp_path))
    assert len(inv.programs) == 0
    assert len(inv.copybooks) == 0
    assert len(inv.jcl_jobs) == 0


def test_mixed_workspace(tmp_path):
    (tmp_path / "PGM1.cbl").write_text("IDENTIFICATION DIVISION.")
    (tmp_path / "PGM2.COB").write_text("IDENTIFICATION DIVISION.")
    (tmp_path / "CPY1.cpy").write_text("01 FIELD PIC X.")
    (tmp_path / "JOB1.jcl").write_text("//JOB JOB")
    (tmp_path / "README.md").write_text("readme")
    inv = scan_workspace(str(tmp_path))
    assert len(inv.programs) == 2
    assert len(inv.copybooks) == 1
    assert len(inv.jcl_jobs) == 1


def test_sha256_is_hex64(tmp_path):
    (tmp_path / "TEST.cbl").write_text("IDENTIFICATION DIVISION.")
    inv = scan_workspace(str(tmp_path))
    assert len(inv.programs[0].sha256) == 64


def test_relative_paths_for_nested_files(tmp_path):
    sub = tmp_path / "src" / "cobol"
    sub.mkdir(parents=True)
    (sub / "NESTED.cbl").write_text("IDENTIFICATION DIVISION.")
    inv = scan_workspace(str(tmp_path))
    assert inv.programs[0].relative_path == str(Path("src") / "cobol" / "NESTED.cbl")


def test_workspace_path_is_resolved(tmp_path):
    (tmp_path / "PGM.cbl").write_text("IDENTIFICATION DIVISION.")
    inv = scan_workspace(str(tmp_path))
    assert Path(inv.workspace_path).is_absolute()
