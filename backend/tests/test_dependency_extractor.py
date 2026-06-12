import pytest

from src.indexing.dependency_extractor import DependencyKind, extract_dependencies


# --- CALL ---

def test_extracts_call_single_quote(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           CALL 'CEEGMT' USING BY REFERENCE GMT-LILIAN\n")
    refs = extract_dependencies(str(f))
    assert len(refs) == 1
    r = refs[0]
    assert r.kind == DependencyKind.CALL
    assert r.target == "CEEGMT"
    assert r.target_is_literal is True
    assert r.line == 1


def test_extracts_call_double_quote(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text('           CALL "CEEDAYS" USING DATE-OF-BIRTH\n')
    refs = extract_dependencies(str(f))
    assert refs[0].target == "CEEDAYS"
    assert refs[0].target_is_literal is True


def test_extracts_dynamic_call(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           CALL WS-PROGRAM-NAME USING WS-DATA\n")
    refs = extract_dependencies(str(f))
    assert refs[0].kind == DependencyKind.CALL
    assert refs[0].target == "WS-PROGRAM-NAME"
    assert refs[0].target_is_literal is False


def test_skips_call_in_comment(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("123456*    CALL 'IGNORED' USING DATA\n"
                 "           CALL 'REAL' USING DATA\n")
    refs = extract_dependencies(str(f))
    assert len(refs) == 1
    assert refs[0].target == "REAL"


# --- PERFORM ---

def test_extracts_perform(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           PERFORM PROCESS-DATA.\n")
    refs = extract_dependencies(str(f))
    assert len(refs) == 1
    r = refs[0]
    assert r.kind == DependencyKind.PERFORM
    assert r.target == "PROCESS-DATA"


def test_extracts_perform_thru(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           PERFORM PROCESS-DATA THRU PROCESS-DATA-END.\n")
    refs = extract_dependencies(str(f))
    assert refs[0].target == "PROCESS-DATA"


def test_extracts_perform_varying_with_paragraph(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           PERFORM POPULATE-ACC VARYING WS-CNT FROM 1 BY 1\n")
    refs = extract_dependencies(str(f))
    assert refs[0].target == "POPULATE-ACC"


def test_skips_inline_perform_varying(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           PERFORM VARYING WS-IDX FROM 1 BY 1 UNTIL WS-IDX > 10\n")
    refs = extract_dependencies(str(f))
    perform_refs = [r for r in refs if r.kind == DependencyKind.PERFORM]
    assert len(perform_refs) == 0


# --- EXEC CICS ---

def test_extracts_exec_cics_return(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           EXEC CICS RETURN\n"
                 "           END-EXEC\n")
    refs = extract_dependencies(str(f))
    cics = [r for r in refs if r.kind == DependencyKind.EXEC_CICS]
    assert len(cics) == 1
    assert cics[0].target == "RETURN"
    assert cics[0].detail is None


def test_extracts_exec_cics_link_with_program(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           EXEC CICS LINK PROGRAM(WS-ABEND-PGM)\n"
                 "           END-EXEC\n")
    refs = extract_dependencies(str(f))
    cics = [r for r in refs if r.kind == DependencyKind.EXEC_CICS]
    assert cics[0].target == "LINK"
    assert cics[0].detail == "WS-ABEND-PGM"


def test_extracts_exec_cics_link_with_literal_program(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           EXEC CICS LINK PROGRAM('MYPGM')\n"
                 "           END-EXEC\n")
    refs = extract_dependencies(str(f))
    cics = [r for r in refs if r.kind == DependencyKind.EXEC_CICS]
    assert cics[0].detail == "MYPGM"


def test_extracts_exec_cics_multiline(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           EXEC CICS SEND\n"
                 "               MAP('BNK1ACC')\n"
                 "               MAPSET('BNK1A')\n"
                 "           END-EXEC\n")
    refs = extract_dependencies(str(f))
    cics = [r for r in refs if r.kind == DependencyKind.EXEC_CICS]
    assert cics[0].target == "SEND"


# --- EXEC SQL ---

def test_extracts_exec_sql_select_from(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           EXEC SQL\n"
                 "              SELECT NAME INTO :HV-NAME\n"
                 "              FROM CUSTOMER\n"
                 "              WHERE ID = :HV-ID\n"
                 "           END-EXEC\n")
    refs = extract_dependencies(str(f))
    sql = [r for r in refs if r.kind == DependencyKind.EXEC_SQL]
    assert len(sql) == 1
    assert sql[0].target == "SELECT"
    assert sql[0].detail == "CUSTOMER"


def test_extracts_exec_sql_insert_into(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           EXEC SQL\n"
                 "              INSERT INTO ACCOUNT VALUES(:HV-ACC)\n"
                 "           END-EXEC\n")
    refs = extract_dependencies(str(f))
    sql = [r for r in refs if r.kind == DependencyKind.EXEC_SQL]
    assert sql[0].target == "INSERT"
    assert sql[0].detail == "ACCOUNT"


def test_extracts_exec_sql_update(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           EXEC SQL\n"
                 "              UPDATE CUSTOMER SET NAME = :HV-NAME\n"
                 "           END-EXEC\n")
    refs = extract_dependencies(str(f))
    sql = [r for r in refs if r.kind == DependencyKind.EXEC_SQL]
    assert sql[0].target == "UPDATE"
    assert sql[0].detail == "CUSTOMER"


def test_extracts_exec_sql_include(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           EXEC SQL\n"
                 "              INCLUDE CUSTDB2\n"
                 "           END-EXEC\n")
    refs = extract_dependencies(str(f))
    sql = [r for r in refs if r.kind == DependencyKind.EXEC_SQL]
    assert sql[0].target == "INCLUDE"
    assert sql[0].detail == "CUSTDB2"


def test_extracts_exec_sql_commit_no_table(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           EXEC SQL COMMIT WORK END-EXEC\n")
    refs = extract_dependencies(str(f))
    sql = [r for r in refs if r.kind == DependencyKind.EXEC_SQL]
    assert sql[0].target == "COMMIT"
    assert sql[0].detail is None


def test_deduplicates_sql_tables_in_one_block(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text("           EXEC SQL\n"
                 "              SELECT A.ID, B.NAME\n"
                 "              FROM CUSTOMER A JOIN CUSTOMER B ON A.ID = B.ID\n"
                 "           END-EXEC\n")
    refs = extract_dependencies(str(f))
    sql = [r for r in refs if r.kind == DependencyKind.EXEC_SQL]
    # CUSTOMER appears twice (FROM + JOIN) but should be deduplicated
    assert len(sql) == 1
    assert sql[0].detail == "CUSTOMER"


# --- mixed program ---

def test_mixed_program_multiple_kinds(tmp_path):
    f = tmp_path / "PGM.cbl"
    f.write_text(
        "           PERFORM VALIDATE-DATA.\n"
        "           CALL 'SUBROUTINE' USING WS-DATA.\n"
        "           EXEC CICS RETURN END-EXEC\n"
        "           EXEC SQL SELECT ID FROM CUSTOMER END-EXEC\n"
    )
    refs = extract_dependencies(str(f))
    kinds = {r.kind for r in refs}
    assert DependencyKind.PERFORM in kinds
    assert DependencyKind.CALL in kinds
    assert DependencyKind.EXEC_CICS in kinds
    assert DependencyKind.EXEC_SQL in kinds


def test_missing_file_returns_empty():
    refs = extract_dependencies("/nonexistent/path/PGM.cbl")
    assert refs == []
