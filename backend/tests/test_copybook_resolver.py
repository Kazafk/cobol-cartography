from pathlib import Path

import pytest

from src.indexing.copybook_resolver import extract_copy_statements, resolve_copybooks
from src.indexing.scanner import FileKind, SourceFile


def make_source(path: str) -> SourceFile:
    return SourceFile(path=path, relative_path=path, kind=FileKind.PROGRAM, size_bytes=0, sha256="")


def make_copybook(path: str) -> SourceFile:
    return SourceFile(path=path, relative_path=path, kind=FileKind.COPYBOOK, size_bytes=0, sha256="")


# --- extract_copy_statements ---

def test_extracts_simple_copy(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("       COPY ABNDINFO.\n")
    stmts = extract_copy_statements(str(f))
    assert stmts == [("ABNDINFO", 1)]


def test_extracts_multiple_copies(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text(
        "       COPY CUSTDATA.\n"
        "       COPY SORTCODE.\n"
    )
    stmts = extract_copy_statements(str(f))
    assert len(stmts) == 2
    assert stmts[0] == ("CUSTDATA", 1)
    assert stmts[1] == ("SORTCODE", 2)


def test_skips_comment_lines(tmp_path):
    f = tmp_path / "PGM.cbl"
    # Column 7 asterisk = comment in fixed format
    f.write_text("123456*      COPY COMMENTED.\n"
                 "       COPY REAL.\n")
    stmts = extract_copy_statements(str(f))
    assert len(stmts) == 1
    assert stmts[0][0] == "REAL"


def test_member_name_uppercased(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("       copy lowercase.\n")
    stmts = extract_copy_statements(str(f))
    assert stmts[0][0] == "LOWERCASE"


def test_returns_correct_line_numbers(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("       IDENTIFICATION DIVISION.\n"
                 "       ENVIRONMENT DIVISION.\n"
                 "       COPY MYBOOK.\n")
    stmts = extract_copy_statements(str(f))
    assert stmts[0] == ("MYBOOK", 3)


def test_missing_file_returns_empty():
    stmts = extract_copy_statements("/nonexistent/path.cbl")
    assert stmts == []


# --- resolve_copybooks ---

def test_resolves_against_known_copybooks(tmp_path):
    pgm = tmp_path / "PGM.cbl"
    pgm.write_text("       COPY CUSTDATA.\n")
    cpy = tmp_path / "copybooks" / "CUSTDATA.cpy"
    cpy.parent.mkdir()
    cpy.write_text("01 FIELD PIC X.")

    programs = [make_source(str(pgm))]
    known = [make_copybook(str(cpy))]
    refs = resolve_copybooks(programs, known)

    assert len(refs) == 1
    assert refs[0].member_name == "CUSTDATA"
    assert refs[0].is_resolved is True
    assert refs[0].resolved_path == str(cpy)


def test_resolves_via_extra_search_path(tmp_path):
    pgm = tmp_path / "PGM.cbl"
    pgm.write_text("       COPY EXTERNAL.\n")
    ext_dir = tmp_path / "external"
    ext_dir.mkdir()
    (ext_dir / "EXTERNAL.cpy").write_text("01 FIELD PIC X.")

    programs = [make_source(str(pgm))]
    refs = resolve_copybooks(programs, [], extra_search_paths=[str(ext_dir)])

    assert refs[0].is_resolved is True


def test_flags_unresolved_copybook(tmp_path):
    pgm = tmp_path / "PGM.cbl"
    pgm.write_text("       COPY MISSING.\n")

    refs = resolve_copybooks([make_source(str(pgm))], [])

    assert refs[0].member_name == "MISSING"
    assert refs[0].is_resolved is False
    assert refs[0].resolved_path is None


def test_case_insensitive_stem_matching(tmp_path):
    pgm = tmp_path / "PGM.cbl"
    pgm.write_text("       COPY CUSTOMER.\n")
    cpy = tmp_path / "customer.cpy"  # lowercase filename
    cpy.write_text("01 FIELD PIC X.")

    programs = [make_source(str(pgm))]
    known = [make_copybook(str(cpy))]
    refs = resolve_copybooks(programs, known)

    assert refs[0].is_resolved is True


def test_extracts_exec_sql_include(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text(
        "       EXEC SQL\n"
        "           INCLUDE CUSTDB2\n"
        "       END-EXEC.\n"
    )
    stmts = extract_copy_statements(str(f))
    assert stmts == [("CUSTDB2", 2)]


def test_extracts_inline_exec_sql_include(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("       EXEC SQL INCLUDE SQLCA END-EXEC.\n")
    stmts = extract_copy_statements(str(f))
    assert stmts == [("SQLCA", 1)]


def test_sql_include_and_copy_together(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text(
        "       COPY HEADER.\n"
        "       EXEC SQL\n"
        "           INCLUDE CUSTDB2\n"
        "       END-EXEC.\n"
        "       COPY FOOTER.\n"
    )
    stmts = extract_copy_statements(str(f))
    names = [s[0] for s in stmts]
    assert names == ["HEADER", "CUSTDB2", "FOOTER"]


def test_sql_select_does_not_produce_include_ref(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text(
        "       EXEC SQL\n"
        "           SELECT * FROM CUSTOMER\n"
        "       END-EXEC.\n"
    )
    stmts = extract_copy_statements(str(f))
    assert stmts == []


def test_mixed_resolved_and_unresolved(tmp_path):
    pgm = tmp_path / "PGM.cbl"
    pgm.write_text("       COPY PRESENT.\n"
                   "       COPY ABSENT.\n")
    cpy = tmp_path / "PRESENT.cpy"
    cpy.write_text("01 FIELD PIC X.")

    programs = [make_source(str(pgm))]
    known = [make_copybook(str(cpy))]
    refs = resolve_copybooks(programs, known)

    resolved = [r for r in refs if r.is_resolved]
    unresolved = [r for r in refs if not r.is_resolved]
    assert len(resolved) == 1
    assert len(unresolved) == 1
    assert unresolved[0].member_name == "ABSENT"
