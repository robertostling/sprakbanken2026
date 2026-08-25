#!/usr/bin/env python3
"""
Interactive CLI for annotating temporal multilingual QA dataset entries.

Run:
    python3 scripts/create_entry.py
    python3 scripts/create_entry.py --username alice
"""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from schema import (
    DateAnswerItem,
    DateEntry,
    DateLanguageAnswers,
    DateRange,
    DateRangeAnswerItem,
    DateRangeEntry,
    DateRangeLanguageAnswers,
    Question,
)

# Default username variable (can be changed directly here or via --username flag)
USERNAME = "main"


def prompt_input(prompt_text: str, default: str = None, required: bool = True) -> str:
    """Prompt user for string input with validation."""
    while True:
        try:
            suffix = f" [{default}]" if default else ""
            user_val = input(f"{prompt_text}{suffix}: ").strip()
            if not user_val and default is not None:
                return default
            if not user_val and required:
                print("  ⚠️  Value cannot be empty. Please try again.")
                continue
            return user_val
        except (KeyboardInterrupt, EOFError):
            print("\n\nOperation cancelled.")
            sys.exit(0)


def prompt_yes_no(prompt_text: str, default: bool = False) -> bool:
    """Prompt user for a yes/no response."""
    default_str = "Y/n" if default else "y/N"
    while True:
        val = prompt_input(f"{prompt_text} ({default_str})", default="y" if default else "n", required=False).lower()
        if val in ["y", "yes"]:
            return True
        if val in ["n", "no"]:
            return False
        print("  ⚠️  Please enter 'y' (yes) or 'n' (no).")


def prompt_language(prompt_text: str = "Language (3-letter ISO code, e.g. ENG, SWE)") -> str:
    """Prompt user for a 3-letter uppercase language code."""
    while True:
        lang = prompt_input(prompt_text).upper()
        if re.match(r"^[A-Z]{2,4}$", lang):
            return lang
        print("  ⚠️  Please enter a valid uppercase language code (e.g. ENG, SWE, DEU).")


def prompt_date(prompt_text: str = "Date (YYYY-MM-DD)") -> datetime.date:
    """Prompt user for a valid ISO date."""
    while True:
        date_str = prompt_input(prompt_text)
        try:
            return datetime.date.fromisoformat(date_str)
        except ValueError:
            print("  ⚠️  Invalid date format. Expected YYYY-MM-DD (e.g. 2026-01-01).")


def prompt_choice(prompt_text: str, choices: list[str]) -> str:
    """Prompt user to select from a list of choices."""
    choices_display = "/".join(choices)
    while True:
        choice = prompt_input(f"{prompt_text} ({choices_display})").lower()
        for c in choices:
            if choice == c.lower():
                return c
        print(f"  ⚠️  Invalid choice. Available options: {choices_display}")


def get_next_filename(output_dir: Path) -> Path:
    """Find the next sequentially numbered json file (e.g., 001.json, 002.json)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_files = list(output_dir.glob("*.json"))
    max_num = 0

    for f in existing_files:
        stem = f.stem
        if stem.isdigit():
            max_num = max(max_num, int(stem))

    next_num = max_num + 1
    return output_dir / f"{next_num:03d}.json"


def collect_questions() -> list[Question]:
    """Interactively collect questions across one or more languages."""
    questions: list[Question] = []
    print("\n--- 1. QUESTIONS ---")

    # First question
    q_text = prompt_input("Question")
    q_lang = prompt_language("Language for this question (e.g. ENG)")
    questions.append(Question(question=q_text, language=q_lang))

    # Additional questions in other languages
    while prompt_yes_no("Do you want to add the same question in a different language?"):
        q_text = prompt_input("Question")
        q_lang = prompt_language("Language for this question (e.g. SWE)")
        questions.append(Question(question=q_text, language=q_lang))

    return questions


def collect_date_answers_for_lang(lang: str) -> list[DateAnswerItem]:
    """Collect point-in-time date answers for a given language."""
    items: list[DateAnswerItem] = []
    while True:
        print(f"\nAdding date answer for [{lang}]:")
        ans = prompt_input("  Answer text")
        d = prompt_date("  Date (YYYY-MM-DD)")
        src = prompt_input("  Source (URL or citation)")
        items.append(DateAnswerItem(date=d, answer=ans, source=src))

        if not prompt_yes_no(f"Do you want to add another answer in [{lang}]?"):
            break
    return items


def collect_daterange_answers_for_lang(lang: str) -> list[DateRangeAnswerItem]:
    """Collect date-range answers for a given language."""
    items: list[DateRangeAnswerItem] = []
    while True:
        print(f"\nAdding date-range answer for [{lang}]:")
        ans = prompt_input("  Answer text")
        from_d = prompt_date("  From Date (YYYY-MM-DD)")
        to_d = prompt_date("  To Date (YYYY-MM-DD)")
        src = prompt_input("  Source (URL or citation)")
        items.append(
            DateRangeAnswerItem(
                date_range=DateRange(from_date=from_d, to_date=to_d),
                answer=ans,
                source=src,
            )
        )

        if not prompt_yes_no(f"Do you want to add another answer in [{lang}]?"):
            break
    return items


def create_entry_interactive(username: str) -> None:
    """Run full interactive flow to create and save a new QA entry."""
    print("=" * 60)
    print(f"  Multilingual QA Entry Creator  |  User: {username}")
    print("=" * 60)

    # 1. Questions
    questions = collect_questions()

    # 2. Answer mode selection (locked for entire entry)
    print("\n--- 2. ANSWERS ---")
    entry_mode = prompt_choice(
        "Select answer temporal type for this entry", choices=["date", "date_range"]
    )
    print(f"🔒 Temporal type locked to: '{entry_mode}' for this entry.")

    # 3. Answer collection loop by language
    first_lang = questions[0].language if questions else "ENG"
    current_lang = prompt_input(
        f"Language of answers", default=first_lang
    ).upper()

    if entry_mode == "date":
        date_groups: list[DateLanguageAnswers] = []
        # First language
        ans_items = collect_date_answers_for_lang(current_lang)
        date_groups.append(DateLanguageAnswers(language=current_lang, answers=ans_items))

        # Other languages
        while True:
            other_lang_input = prompt_input(
                "Do you want to add answers in a different language? (enter 3-letter code or 'no')",
                default="no",
            )
            if other_lang_input.lower() in ["no", "n"]:
                break
            other_lang = other_lang_input.upper()
            ans_items = collect_date_answers_for_lang(other_lang)
            date_groups.append(DateLanguageAnswers(language=other_lang, answers=ans_items))

        entry_obj = DateEntry(questions=questions, answers=date_groups)

    else:
        daterange_groups: list[DateRangeLanguageAnswers] = []
        # First language
        ans_items = collect_daterange_answers_for_lang(current_lang)
        daterange_groups.append(DateRangeLanguageAnswers(language=current_lang, answers=ans_items))

        # Other languages
        while True:
            other_lang_input = prompt_input(
                "Do you want to add answers in a different language? (enter 3-letter code or 'no')",
                default="no",
            )
            if other_lang_input.lower() in ["no", "n"]:
                break
            other_lang = other_lang_input.upper()
            ans_items = collect_daterange_answers_for_lang(other_lang)
            daterange_groups.append(DateRangeLanguageAnswers(language=other_lang, answers=ans_items))

        entry_obj = DateRangeEntry(questions=questions, answers=daterange_groups)

    # 4. Save to output directory
    output_dir = PROJECT_ROOT / "output" / username
    target_file = get_next_filename(output_dir)

    entry_data = entry_obj.model_dump(by_alias=True, mode="json")
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(entry_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("\n" + "=" * 60)
    print(f"✓ Successfully saved entry to: {target_file.relative_to(PROJECT_ROOT)}")
    print("=" * 60)
    print(json.dumps(entry_data, indent=2, ensure_ascii=False))
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Interactive temporal QA dataset entry tool.")
    parser.add_argument(
        "--username",
        "-u",
        default=USERNAME,
        help=f"Username for output subdirectory (default: '{USERNAME}')",
    )
    args = parser.parse_args()

    while True:
        create_entry_interactive(username=args.username)
        if not prompt_yes_no("\nDo you want to create another entry?", default=False):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
