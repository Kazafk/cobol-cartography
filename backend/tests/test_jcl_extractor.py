from src.indexing.jcl_extractor import JclRefKind, extract_jcl_dependencies

_SAMPLE = """\
//DB2BIND JOB 'DB2',NOTIFY=&SYSUID,CLASS=A,MSGCLASS=H
//          MSGLEVEL=(1,1),REGION=4M
//BIND    EXEC PGM=IKJEFT01
//STEPLIB  DD  DISP=SHR,DSN=DB2V13.SDSNEXIT
//         DD  DISP=SHR,DSN=DB2V13.SDSNLOAD
//DBRMLIB  DD DISP=SHR,DSN=BANKZ.V0R1M0.DBRM(BANKDATA)
//SYSPRINT DD  SYSOUT=*
//* This is a comment
//GRANT   EXEC PGM=IKJEFT01,REGION=0M
//CALLPROC EXEC PROC=MYPROC
//IMPPROC  EXEC MYPROC2
"""


def _write(tmp_path, content):
    f = tmp_path / "TEST.jcl"
    f.write_text(content)
    return str(f)


def test_extracts_job_statement(tmp_path):
    refs = extract_jcl_dependencies(_write(tmp_path, _SAMPLE))
    jobs = [r for r in refs if r.kind == JclRefKind.JOB]
    assert len(jobs) == 1
    assert jobs[0].name == "DB2BIND"
    assert jobs[0].line == 1


def test_extracts_exec_pgm(tmp_path):
    refs = extract_jcl_dependencies(_write(tmp_path, _SAMPLE))
    execs = [r for r in refs if r.kind == JclRefKind.EXEC_PGM]
    assert len(execs) == 2
    assert all(r.target == "IKJEFT01" for r in execs)
    names = {r.name for r in execs}
    assert names == {"BIND", "GRANT"}


def test_extracts_explicit_proc(tmp_path):
    refs = extract_jcl_dependencies(_write(tmp_path, _SAMPLE))
    procs = [r for r in refs if r.kind == JclRefKind.EXEC_PROC]
    assert any(r.name == "CALLPROC" and r.target == "MYPROC" for r in procs)


def test_extracts_implicit_proc(tmp_path):
    refs = extract_jcl_dependencies(_write(tmp_path, _SAMPLE))
    procs = [r for r in refs if r.kind == JclRefKind.EXEC_PROC]
    assert any(r.name == "IMPPROC" and r.target == "MYPROC2" for r in procs)


def test_extracts_dd_with_dsn(tmp_path):
    refs = extract_jcl_dependencies(_write(tmp_path, _SAMPLE))
    dds = [r for r in refs if r.kind == JclRefKind.DD]
    steplib = next(r for r in dds if r.name == "STEPLIB")
    assert steplib.target == "DB2V13.SDSNEXIT"


def test_extracts_dd_without_dsn(tmp_path):
    refs = extract_jcl_dependencies(_write(tmp_path, _SAMPLE))
    dds = [r for r in refs if r.kind == JclRefKind.DD]
    sysprint = next(r for r in dds if r.name == "SYSPRINT")
    assert sysprint.target is None


def test_skips_comments(tmp_path):
    refs = extract_jcl_dependencies(_write(tmp_path, _SAMPLE))
    # No ref should come from the comment line
    assert all(r.line != 8 for r in refs)


def test_skips_continuation_lines(tmp_path):
    refs = extract_jcl_dependencies(_write(tmp_path, _SAMPLE))
    # Line 2 is continuation (//          MSGLEVEL...) — no separate ref
    assert all(r.line != 2 for r in refs)


def test_missing_file_returns_empty():
    assert extract_jcl_dependencies("/nonexistent/path.jcl") == []


def test_line_numbers_are_correct(tmp_path):
    content = "//MYJOB  JOB CLASS=A\n//STEP1  EXEC PGM=MYPGM\n"
    refs = extract_jcl_dependencies(_write(tmp_path, content))
    job = next(r for r in refs if r.kind == JclRefKind.JOB)
    step = next(r for r in refs if r.kind == JclRefKind.EXEC_PGM)
    assert job.line == 1
    assert step.line == 2
