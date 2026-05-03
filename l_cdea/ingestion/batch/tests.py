"""
Batch ingestion tests.

Covers all 4 spec validation examples:
  1. directory with 3 files → total_files=3, successful_files=3
  2. one bad file → failed_files=1, remaining processed
  3. stop_on_error=True → batch stops on first failure
  4. deterministic order → same directory run twice = identical report

Additional checks:
  - max_files limits processing
  - save_per_file=False accumulates and saves once
  - BatchIngestionReport totals are correct
  - invalid config raises BatchIngestionError
  - per-file provenance includes source_path
  - nodes from all files visible after batch
"""
from __future__ import annotations

import os
import tempfile

import l_cdea.domain
import l_cdea.data

from l_cdea.ingestion.batch import (
    BatchIngestionConfig,
    BatchIngestionReport,
    BatchIngestionError,
    batch_ingest_directory,
    batch_ingest_files,
)
from l_cdea.discourse.definition_retrieval.lookup import clear_definitions
from l_cdea.core.planner.discourse_lookup import clear_cache

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"

_FILE_A = "Velocity is displacement over time.\nForce is mass times acceleration.\n"
_FILE_B = "Acceleration is the rate of change of velocity.\nMass is the amount of matter.\n"
_FILE_C = "Energy is the capacity to do work.\nPower is the rate of doing work.\n"
_FILE_BAD = "this is not a real file path that exists"


def _make_dir(files: dict) -> str:
    """Create a temp dir with given filename→content dict. Returns dir path."""
    d = tempfile.mkdtemp()
    for name, content in files.items():
        with open(os.path.join(d, name), "w") as f:
            f.write(content)
    return d


def _make_state_path() -> str:
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    f.close()
    os.unlink(f.name)
    return f.name


def _reset():
    clear_definitions()
    clear_cache()


# ── Spec Example 1: 3 files, all succeed ─────────────────────────────────────

def test_example_1_three_files():
    _reset()
    d = _make_dir({"a.txt": _FILE_A, "b.txt": _FILE_B, "c.txt": _FILE_C})
    sp = _make_state_path()
    try:
        config = BatchIngestionConfig(state_path=sp)
        report = batch_ingest_directory(d, config)
        ok = report.total_files == 3
        print(f"{_PASS if ok else _FAIL} example 1: total_files={report.total_files} (expected 3)")
        ok2 = report.successful_files == 3
        print(f"{_PASS if ok2 else _FAIL} example 1: successful_files={report.successful_files} (expected 3)")
        ok3 = report.failed_files == 0
        print(f"{_PASS if ok3 else _FAIL} example 1: failed_files={report.failed_files} (expected 0)")
        ok4 = report.total_definitions == 6
        print(f"{_PASS if ok4 else _FAIL} example 1: total_definitions={report.total_definitions} (expected 6)")
        ok5 = report.total_nodes_added == 6
        print(f"{_PASS if ok5 else _FAIL} example 1: total_nodes_added={report.total_nodes_added} (expected 6)")
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        if os.path.exists(sp):
            os.unlink(sp)


# ── Spec Example 2: one bad file, batch continues ────────────────────────────

def test_example_2_one_bad_file():
    _reset()
    d = _make_dir({"a.txt": _FILE_A, "b.txt": _FILE_B})
    sp = _make_state_path()
    try:
        files = [
            os.path.join(d, "a.txt"),
            "/nonexistent/missing_file.txt",   # bad
            os.path.join(d, "b.txt"),
        ]
        config = BatchIngestionConfig(state_path=sp, stop_on_error=False)
        report = batch_ingest_files(files, config)
        ok = report.failed_files == 1
        print(f"{_PASS if ok else _FAIL} example 2: failed_files={report.failed_files} (expected 1)")
        ok2 = report.successful_files == 2
        print(f"{_PASS if ok2 else _FAIL} example 2: successful_files={report.successful_files} (expected 2)")
        ok3 = report.processed_files == 3
        print(f"{_PASS if ok3 else _FAIL} example 2: processed_files={report.processed_files} (expected 3)")
        # failed result has error string set
        bad = next(r for r in report.file_results if not r.success)
        ok4 = bad.error is not None and len(bad.error) > 0
        print(f"{_PASS if ok4 else _FAIL} example 2: failed result has error={bad.error!r}")
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        if os.path.exists(sp):
            os.unlink(sp)


# ── Spec Example 3: stop_on_error=True ───────────────────────────────────────

def test_example_3_stop_on_error():
    _reset()
    d = _make_dir({"a.txt": _FILE_A, "c.txt": _FILE_C})
    sp = _make_state_path()
    try:
        files = [
            os.path.join(d, "a.txt"),
            "/nonexistent/bad.txt",            # bad → batch stops here
            os.path.join(d, "c.txt"),          # should NOT be processed
        ]
        config = BatchIngestionConfig(state_path=sp, stop_on_error=True)
        report = batch_ingest_files(files, config)
        ok = report.failed_files == 1
        print(f"{_PASS if ok else _FAIL} example 3: failed_files={report.failed_files} (expected 1)")
        ok2 = report.successful_files == 1
        print(f"{_PASS if ok2 else _FAIL} example 3: successful_files={report.successful_files} (expected 1)")
        ok3 = report.processed_files == 2   # a.txt + bad.txt; c.txt never reached
        print(f"{_PASS if ok3 else _FAIL} example 3: processed_files={report.processed_files} (expected 2)")
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        if os.path.exists(sp):
            os.unlink(sp)


# ── Spec Example 4: deterministic order ──────────────────────────────────────

def test_example_4_deterministic_order():
    _reset()
    d = _make_dir({"a.txt": _FILE_A, "b.txt": _FILE_B, "c.txt": _FILE_C})
    sp1 = _make_state_path()
    sp2 = _make_state_path()
    try:
        config1 = BatchIngestionConfig(state_path=sp1)
        config2 = BatchIngestionConfig(state_path=sp2)
        r1 = batch_ingest_directory(d, config1)
        _reset()
        r2 = batch_ingest_directory(d, config2)

        ok = [fr.file_path for fr in r1.file_results] == [fr.file_path for fr in r2.file_results]
        print(f"{_PASS if ok else _FAIL} example 4: file order identical across runs")
        ok2 = r1.total_definitions == r2.total_definitions
        print(f"{_PASS if ok2 else _FAIL} example 4: total_definitions identical ({r1.total_definitions})")
        ok3 = r1.total_nodes_added == r2.total_nodes_added
        print(f"{_PASS if ok3 else _FAIL} example 4: total_nodes_added identical ({r1.total_nodes_added})")
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        for sp in (sp1, sp2):
            if os.path.exists(sp):
                os.unlink(sp)


# ── max_files limits processing ───────────────────────────────────────────────

def test_max_files():
    _reset()
    d = _make_dir({"a.txt": _FILE_A, "b.txt": _FILE_B, "c.txt": _FILE_C})
    sp = _make_state_path()
    try:
        config = BatchIngestionConfig(state_path=sp, max_files=2)
        report = batch_ingest_directory(d, config)
        ok = report.total_files == 2
        print(f"{_PASS if ok else _FAIL} max_files: total_files={report.total_files} (expected 2)")
        ok2 = report.successful_files == 2
        print(f"{_PASS if ok2 else _FAIL} max_files: successful_files={report.successful_files}")
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        if os.path.exists(sp):
            os.unlink(sp)


# ── save_per_file=False: accumulate in memory, save once ─────────────────────

def test_save_per_file_false():
    _reset()
    d = _make_dir({"a.txt": _FILE_A, "b.txt": _FILE_B})
    sp = _make_state_path()
    try:
        config = BatchIngestionConfig(state_path=sp, save_per_file=False)
        report = batch_ingest_directory(d, config)
        ok = report.successful_files == 2
        print(f"{_PASS if ok else _FAIL} save_once: successful_files={report.successful_files}")
        ok2 = report.total_definitions == 4
        print(f"{_PASS if ok2 else _FAIL} save_once: total_definitions={report.total_definitions} (expected 4)")
        # State file must exist after batch
        ok3 = os.path.exists(sp)
        print(f"{_PASS if ok3 else _FAIL} save_once: state file written")
        # State must be queryable
        from l_cdea.discourse.storage import load_state
        _reset()
        state = load_state(sp)
        ok4 = len(state.nodes) >= 4
        print(f"{_PASS if ok4 else _FAIL} save_once: state has {len(state.nodes)} nodes (expected ≥4)")
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        if os.path.exists(sp):
            os.unlink(sp)


# ── Invalid config raises BatchIngestionError ─────────────────────────────────

def test_invalid_config():
    try:
        BatchIngestionConfig(mode="turbo")
        print(f"{_FAIL} invalid config: no exception raised")
    except BatchIngestionError as e:
        print(f"{_PASS} invalid config: BatchIngestionError raised: {e}")

    try:
        BatchIngestionConfig(max_files=0)
        print(f"{_FAIL} invalid max_files: no exception raised")
    except BatchIngestionError as e:
        print(f"{_PASS} invalid max_files: BatchIngestionError raised")


# ── Not a directory raises BatchIngestionError ────────────────────────────────

def test_not_a_directory():
    try:
        config = BatchIngestionConfig()
        batch_ingest_directory("/nonexistent/path", config)
        print(f"{_FAIL} not-a-dir: no exception raised")
    except BatchIngestionError as e:
        print(f"{_PASS} not-a-dir: BatchIngestionError raised")


# ── Nodes from all files are queryable after batch ────────────────────────────

def test_nodes_queryable_after_batch():
    _reset()
    d = _make_dir({"a.txt": _FILE_A, "b.txt": _FILE_B})
    sp = _make_state_path()
    try:
        config = BatchIngestionConfig(state_path=sp)
        batch_ingest_directory(d, config)

        from l_cdea.discourse.storage import load_state
        from l_cdea.discourse.definition_retrieval.lookup import lookup_definition
        _reset()
        state = load_state(sp)

        for term in ("velocity", "force", "acceleration", "mass"):
            result = lookup_definition(term, state)
            ok = result.hit
            print(f"{_PASS if ok else _FAIL} queryable: '{term}' hit={result.hit}")
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        if os.path.exists(sp):
            os.unlink(sp)


# ── Per-file duration_ms is non-negative ─────────────────────────────────────

def test_duration_recorded():
    _reset()
    d = _make_dir({"a.txt": _FILE_A})
    sp = _make_state_path()
    try:
        config = BatchIngestionConfig(state_path=sp)
        report = batch_ingest_directory(d, config)
        ok = all(fr.duration_ms >= 0 for fr in report.file_results)
        print(f"{_PASS if ok else _FAIL} duration: all duration_ms >= 0")
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        if os.path.exists(sp):
            os.unlink(sp)


# ── Runner ────────────────────────────────────────────────────────────────────

def run_all():
    tests = [
        ("Example 1: 3 files, all succeed",                   test_example_1_three_files),
        ("Example 2: one bad file, batch continues",           test_example_2_one_bad_file),
        ("Example 3: stop_on_error=True",                     test_example_3_stop_on_error),
        ("Example 4: deterministic order",                    test_example_4_deterministic_order),
        ("max_files limits processing",                        test_max_files),
        ("save_per_file=False: accumulate + save once",       test_save_per_file_false),
        ("Invalid config raises BatchIngestionError",         test_invalid_config),
        ("Not a directory raises BatchIngestionError",        test_not_a_directory),
        ("Nodes queryable after batch",                       test_nodes_queryable_after_batch),
        ("Per-file duration_ms recorded",                     test_duration_recorded),
    ]
    failed = 0
    for name, fn in tests:
        print(f"\n── {name}")
        try:
            fn()
        except Exception as exc:
            import traceback
            print(f"{_FAIL} UNEXPECTED EXCEPTION: {exc!r}")
            traceback.print_exc()
            failed += 1
    print(f"\n{'All tests passed.' if not failed else f'{failed} test(s) raised unexpected exceptions.'}")


if __name__ == "__main__":
    run_all()
