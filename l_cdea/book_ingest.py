"""
CLI entry point for book ingestion.

Usage:
  python3 -m l_cdea.book_ingest <file> [--resume] [--no-resume]
                                        [--state-path PATH] [--max-chapters N]

Options:
  --resume         Resume from last checkpoint (default: True)
  --no-resume      Start fresh, ignoring any existing manifest
  --state-path     Path to the discourse state JSON file
  --max-chapters   Stop after ingesting this many chapters
"""
from __future__ import annotations

import argparse
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m l_cdea.book_ingest",
        description="Ingest a book into the L-CDEA knowledge graph",
    )
    parser.add_argument("file", help="Path to the book file (.txt)")
    parser.add_argument("--resume", dest="resume", action="store_true", default=True,
                        help="Resume from last checkpoint (default)")
    parser.add_argument("--no-resume", dest="resume", action="store_false",
                        help="Start fresh, ignoring existing manifest")
    parser.add_argument("--state-path", default=None,
                        help="Discourse state file path")
    parser.add_argument("--max-chapters", type=int, default=None,
                        help="Stop after N chapters (for incremental ingestion)")
    args = parser.parse_args(argv)

    from l_cdea.ingestion.book_prep.loader import ingest_book

    try:
        trace = ingest_book(
            path=args.file,
            resume=args.resume,
            state_path=args.state_path,
            max_chapters=args.max_chapters,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"=== BOOK INGESTION COMPLETE ===")
    print(f"  book_id:    {trace.book_id}")
    print(f"  chapters:   {trace.chapters_processed}/{trace.chapters_total} processed")
    print(f"  chunks:     {trace.chunks_processed}")
    print(f"  nodes:      {trace.nodes_added}")
    print(f"  edges:      {trace.edges_added}")
    print(f"  resumed:    {trace.resumed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
