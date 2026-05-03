"""
CLI: python3 -m l_cdea.batch_ingest <directory>

Flags:
  --state-path PATH       override default state file path
  --stop-on-error         abort on first file failure
  --no-save-per-file      accumulate in memory, save once at end
  --max-files N           limit number of files processed
  --mode MODE             ingestion mode (default: dictionary)
"""
from __future__ import annotations

import sys

from l_cdea.ingestion.batch import (
    BatchIngestionConfig,
    BatchIngestionError,
    batch_ingest_directory,
)
from l_cdea.ingestion.knowledge_importer import DEFAULT_STATE_PATH


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        print("Usage: python3 -m l_cdea.batch_ingest <directory> [flags]", file=sys.stderr)
        return 1

    directory = argv[0]
    rest = argv[1:]

    state_path = DEFAULT_STATE_PATH
    stop_on_error = False
    save_per_file = True
    max_files = None
    mode = "dictionary"

    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg == "--state-path" and i + 1 < len(rest):
            state_path = rest[i + 1]
            i += 2
        elif arg == "--stop-on-error":
            stop_on_error = True
            i += 1
        elif arg == "--no-save-per-file":
            save_per_file = False
            i += 1
        elif arg == "--max-files" and i + 1 < len(rest):
            try:
                max_files = int(rest[i + 1])
            except ValueError:
                print(f"--max-files requires an integer, got {rest[i+1]!r}", file=sys.stderr)
                return 1
            i += 2
        elif arg == "--mode" and i + 1 < len(rest):
            mode = rest[i + 1]
            i += 2
        else:
            print(f"Unknown flag: {arg!r}", file=sys.stderr)
            return 1

    try:
        config = BatchIngestionConfig(
            mode=mode,
            state_path=state_path,
            stop_on_error=stop_on_error,
            save_per_file=save_per_file,
            max_files=max_files,
        )
    except BatchIngestionError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 1

    print(f"Batch ingesting: {directory}")
    print(f"  mode={config.mode}  state={config.state_path}  "
          f"stop_on_error={config.stop_on_error}  "
          f"save_per_file={config.save_per_file}")

    try:
        report = batch_ingest_directory(directory, config)
    except BatchIngestionError as exc:
        print(f"Batch error: {exc}", file=sys.stderr)
        return 1

    print(f"\n{report}")
    print(f"\nPer-file results:")
    for fr in report.file_results:
        status = "OK" if fr.success else "FAIL"
        name = fr.file_path.split("/")[-1]
        if fr.success and fr.ingestion_result:
            r = fr.ingestion_result
            print(f"  [{status}] {name}: "
                  f"chunks={r.chunks_processed}, "
                  f"definitions={r.definitions}, "
                  f"nodes_added={r.nodes_added}  "
                  f"({fr.duration_ms}ms)")
        else:
            print(f"  [{status}] {name}: {fr.error}  ({fr.duration_ms}ms)")

    return 1 if report.failed_files else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
