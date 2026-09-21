#!/usr/bin/env python3
"""Search the bundled DAMASK troubleshooting cards without external dependencies."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
KB_ROOT = SKILL_ROOT / "references" / "troubleshooting-kb"
CATEGORIES = ("pre", "run", "post", "debug", "advance", "gen")
DEFAULT_LIMIT = 3
MAX_LIMIT = 10
EXPECTED_CARDS = 102
CARD_HEADING = re.compile(r"(?m)^### .+$")
SOURCE_LINK = re.compile(
    r"\[#(?P<number>\d+)\]\(https://github\.com/damask-multiphysics/DAMASK/discussions/(?P=number)\)"
)
TOKEN = re.compile(r"[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*")


class KnowledgeBaseError(RuntimeError):
    """Report malformed or unavailable bundled knowledge."""


@dataclass(frozen=True)
class Card:
    category: str
    text: str
    title: str
    status: str


@dataclass(frozen=True)
class Match:
    score: int
    card: Card


def _status(text: str) -> str:
    lowered = text.casefold()
    if re.search(r"\((?:unanswered|unsolved)(?: in-thread)?\.?\)", lowered):
        return "unresolved upstream"
    if "not fully root-caused" in lowered or "root cause" in lowered and "still open" in lowered:
        return "partial mitigation; root cause open"
    return "solution or maintainer guidance reported"


def load_cards(categories: Iterable[str] = CATEGORIES) -> list[Card]:
    cards: list[Card] = []
    for category in categories:
        if category not in CATEGORIES:
            raise KnowledgeBaseError(f"unknown category: {category}")
        path = KB_ROOT / f"{category}.md"
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            raise KnowledgeBaseError(f"cannot read bundled KB category {category}: {error}") from error
        starts = [match.start() for match in CARD_HEADING.finditer(text)]
        for index, start in enumerate(starts):
            end = starts[index + 1] if index + 1 < len(starts) else len(text)
            card_text = text[start:end].strip()
            title = card_text.splitlines()[0][4:].strip()
            if not SOURCE_LINK.search(title):
                raise KnowledgeBaseError(f"card has no valid source link in {path.name}: {title}")
            cards.append(Card(category, card_text, title, _status(card_text)))
    return cards


def _query_terms(query: str) -> list[str]:
    return list(dict.fromkeys(token.casefold() for token in TOKEN.findall(query)))


def score_card(card: Card, query: str) -> int:
    phrase = " ".join(query.casefold().split())
    terms = _query_terms(query)
    if not phrase or not terms:
        return 0
    title = card.title.casefold()
    text = card.text.casefold()
    problem = text.split("**fix / steps:**", 1)[0]
    score = 0
    if phrase in title:
        score += 140
    elif phrase in text:
        score += 100
    matched = 0
    for term in terms:
        boundary = re.compile(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])")
        if boundary.search(text):
            matched += 1
            score += 12 if boundary.search(title) else 6 if boundary.search(problem) else 2
            if term.isdigit():
                score += 70
    if matched == len(terms):
        score += 25
    return score


def search(query: str, categories: Iterable[str] = CATEGORIES, limit: int = DEFAULT_LIMIT) -> list[Match]:
    if limit < 1 or limit > MAX_LIMIT:
        raise KnowledgeBaseError(f"limit must be between 1 and {MAX_LIMIT}")
    matches = [Match(score_card(card, query), card) for card in load_cards(categories)]
    matches = [match for match in matches if match.score > 0]
    matches.sort(key=lambda match: (-match.score, CATEGORIES.index(match.card.category), match.card.title.casefold()))
    return matches[:limit]


def verify() -> tuple[int, str]:
    cards = load_cards()
    if len(cards) != EXPECTED_CARDS:
        raise KnowledgeBaseError(f"expected {EXPECTED_CARDS} cards, found {len(cards)}")
    return len(cards), f"verified {len(cards)} complete cards across {len(CATEGORIES)} categories"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Search complete, sourced cards in the bundled DAMASK discussion knowledge base."
    )
    result.add_argument("query", nargs="*", help="exact error, symptom, phrase, or DAMASK key")
    result.add_argument(
        "--category",
        action="append",
        choices=CATEGORIES,
        help="search one or more categories (default: all)",
    )
    result.add_argument(
        "--fallback-all",
        action="store_true",
        help="if selected categories have no matches, retry all categories",
    )
    result.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"maximum complete cards (1-{MAX_LIMIT})")
    result.add_argument("--verify", action="store_true", help="validate the bundled KB and exit")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.verify:
            _, message = verify()
            print(message)
            return 0
        query = " ".join(args.query).strip()
        if not query:
            raise KnowledgeBaseError("provide a query or use --verify")
        categories = tuple(dict.fromkeys(args.category or CATEGORIES))
        matches = search(query, categories, args.limit)
        fell_back = False
        if not matches and args.category and args.fallback_all:
            matches = search(query, CATEGORIES, args.limit)
            fell_back = True
        scope = ", ".join(categories)
        if fell_back:
            print(f"No matches in selected categories ({scope}); searched all categories.\n")
        if not matches:
            print(f"No matching troubleshooting cards for {query!r} in {scope}.")
            if args.category and not args.fallback_all:
                print("Retry with no --category, or add --fallback-all.")
            return 1
        print(f"Top {len(matches)} complete card(s) for {query!r}:\n")
        for index, match in enumerate(matches, 1):
            print(f"===== Match {index} | category: {match.card.category} | upstream status: {match.card.status} =====")
            print(match.card.text)
            if index != len(matches):
                print()
        return 0
    except KnowledgeBaseError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
