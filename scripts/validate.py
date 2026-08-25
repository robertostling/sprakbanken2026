#!/usr/bin/env python3
"""Validation utility for QA dataset JSON files using Pydantic models."""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import TypeAdapter, ValidationError
from schema import Dataset, Entry

entry_adapter = TypeAdapter(Entry)


def validate_file(data_path: Path) -> bool:
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        if isinstance(raw, list):
            dataset = Dataset.model_validate(raw)
            print(f"✓ Valid dataset: '{data_path}' ({len(dataset.root)} entries)")
            return True
        elif isinstance(raw, dict):
            entry = entry_adapter.validate_python(raw)
            print(f"✓ Valid single entry: '{data_path}' (Type: {type(entry).__name__})")
            return True
        else:
            print(f"✗ Invalid JSON root type in '{data_path}': expected list or object, got {type(raw).__name__}")
            return False

    except ValidationError as e:
        print(f"✗ Validation failed for '{data_path}':\n")
        for err in e.errors():
            loc = " -> ".join(str(p) for p in err["loc"])
            msg = err["msg"]
            print(f"  - [{loc}]: {msg}")
        return False
    except Exception as e:
        print(f"✗ Error loading '{data_path}': {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate QA dataset or entry JSON files using Pydantic schema classes.")
    parser.add_argument(
        "target",
        nargs="?",
        default="schema/examples.json",
        help="Path to JSON file or directory to validate (default: schema/examples.json)"
    )
    args = parser.parse_args()

    target_path = Path(args.target)
    if not target_path.exists():
        print(f"Error: Path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if target_path.is_dir():
        json_files = sorted(target_path.glob("*.json"))
        if not json_files:
            print(f"No JSON files found in directory '{target_path}'.")
            sys.exit(0)
        all_passed = True
        for jf in json_files:
            if not validate_file(jf):
                all_passed = False
        sys.exit(0 if all_passed else 1)
    else:
        success = validate_file(target_path)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
