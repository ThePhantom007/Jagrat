import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ingest_articles import read_articles  # noqa: E402


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit the organiser-provided Jagrat JSON source")
    parser.add_argument("json_path", type=Path)
    args = parser.parse_args()
    _, stats = read_articles(args.json_path)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    if stats["duplicates_removed"]:
        print("WARNING: exact duplicate source records were found.", file=sys.stderr)
