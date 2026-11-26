"""Build one fortune-cookie line for a software engineer.

This entry targets the make.fun bounty
u-eager-stork-81-9647-fortune-cookie-funnies-for-866bde2a.
It drafts a dozen candidate slips, grades each one on five lenses,
picks the strongest deterministically, and writes it to
/output/entry.txt. The same bytes come out on every run.
"""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import sys

SLIP_HEAD = "Your next deploy will succeed on the first try."
SLIP_TAIL = "Nobody will believe you, least of all you."
WINNER = SLIP_HEAD + " " + SLIP_TAIL

# Lens weights: how a slip reads as a fortune, how hard it lands,
# how clean the wording is, how fresh the joke feels, how tight it is.
LENS_WEIGHT = {"slip": 3, "laugh": 3, "craft": 2, "novelty": 2, "brevity": 1}

# Stock lines a fortune must never recycle.
STALE_LINES = (
    "works on my machine",
    "have you tried turning it off",
    "not a bug, a feature",
    "99 little bugs",
    "10 kinds of people",
    "it works on my machine",
)


@dataclass
class Slip:
    """One candidate: first take, polished take, why it changed, grades."""

    first_take: str
    final_take: str
    edit_note: str
    grades: dict


CANDIDATES = [
    Slip(
        "Your next deploy will succeed on the first try and nobody will believe it, not even you.",
        WINNER,
        "Cut the flat single sentence in two and aimed the disbelief at the reader, so the second half lands like a verdict.",
        {"slip": 10, "laugh": 9, "craft": 10, "novelty": 9, "brevity": 9},
    ),
    Slip(
        "Your on-call shift will pass without a single page, because even the pager needs a night off.",
        "Your on-call shift will be silent all night. The pager knows. It is simply being polite.",
        "Dropped the explaining clause and let the pager itself deliver the joke in three short beats.",
        {"slip": 9, "laugh": 8, "craft": 9, "novelty": 9, "brevity": 8},
    ),
    Slip(
        "A junior will one day ask why this function exists, and you will answer by opening git blame and meeting your younger self.",
        "A junior will ask why this function exists. You will open the blame log and meet your younger self.",
        "Trimmed the throat-clearing and swapped the tool name for the shorter log, so the meeting is the punchline.",
        {"slip": 8, "laugh": 9, "craft": 9, "novelty": 10, "brevity": 8},
    ),
    Slip(
        "Beware the Friday deploy, for the weekend has already filed a complaint against you in your own name.",
        "Beware the Friday deploy. The weekend has already filed a complaint in your name.",
        "Removed the stiff 'for' and let the warning stand on its own before the absurd complaint arrives.",
        {"slip": 9, "laugh": 9, "craft": 8, "novelty": 8, "brevity": 9},
    ),
    Slip(
        "Lucky numbers: 42, 404, and the port number your service has been quietly squatting on since last spring.",
        "Lucky numbers: 42, 404, and the port your service has been quietly squatting on since spring.",
        "Cut 'last' and 'number' where the line already says enough, so the list reads like a real slip.",
        {"slip": 10, "laugh": 7, "craft": 8, "novelty": 8, "brevity": 8},
    ),
    Slip(
        "Your rubber duck is about to resign after hearing the same bug explained to it four times in a row.",
        "Your rubber duck will resign. It has heard the same bug explained four times and still disagrees.",
        "Gave the duck a voice in the second sentence instead of narrating its exit from the outside.",
        {"slip": 8, "laugh": 10, "craft": 8, "novelty": 10, "brevity": 8},
    ),
    Slip(
        "The test suite will pass on the third run even though nobody changed anything at all, because the tests have simply relented.",
        "The test suite will pass on the third run. Nobody changed anything. The tests simply relented.",
        "Broke the ramble into three flat statements; the deadpan delivery is the joke now.",
        {"slip": 9, "laugh": 9, "craft": 8, "novelty": 9, "brevity": 9},
    ),
    Slip(
        "You will delete three hundred lines of code today, and the product will somehow get better because of it, which is not a mistake.",
        "You will delete three hundred lines today and the product will improve. This is not a mistake.",
        "Shed the hedging words so the improvement and the denial hit back to back.",
        {"slip": 8, "laugh": 8, "craft": 10, "novelty": 8, "brevity": 9},
    ),
    Slip(
        "A reviewer will approve your work in four minutes flat, so you should spend the hours you saved wisely by taking a nap.",
        "A code review will approve your work in four minutes. Spend the saved hours wisely: nap.",
        "Named the review, dropped the moralising filler, and ended on a single-word command.",
        {"slip": 7, "laugh": 9, "craft": 8, "novelty": 9, "brevity": 9},
    ),
    Slip(
        "The legacy system will outlive its documentation and its author and also your patience, and it will do so in that exact order.",
        "The legacy system will outlive its documentation, its author, and your patience, in that order.",
        "Folded the trailing explanation into a comma list so the ordering itself becomes the sting.",
        {"slip": 8, "laugh": 8, "craft": 9, "novelty": 7, "brevity": 8},
    ),
    Slip(
        "Your commit message will say small fix, but the diff will tell a very different story in about two thousand four hundred lines.",
        "Your commit message will say 'small fix'. The diff will say otherwise, in 2,400 lines.",
        "Quoted the message, swapped the wordy summary for 'otherwise', and let the exact number do the work.",
        {"slip": 8, "laugh": 9, "craft": 9, "novelty": 8, "brevity": 8},
    ),
    Slip(
        "Somewhere out there a server you forgot you ever started is still running your very first deploy, and it sends its regards.",
        "Somewhere, a server you forgot exists is still running your first deploy. It sends its regards.",
        "Cut the extra clauses and split the sentence so the regards arrive as a postscript.",
        {"slip": 9, "laugh": 8, "craft": 9, "novelty": 9, "brevity": 7},
    ),
]


def total_points(slip):
    """Weighted sum of a candidate's five lens grades."""
    points = 0
    for lens, weight in LENS_WEIGHT.items():
        points += slip.grades[lens] * weight
    return points


def passes_rules(text):
    """A slip must be one line, at most 120 chars, and free of cliches."""
    cleaned = text.strip()
    size_ok = 1 <= len(cleaned) <= 120
    one_line = "\n" not in cleaned and "\r" not in cleaned
    lowered = cleaned.lower()
    fresh = all(stale not in lowered for stale in STALE_LINES)
    return size_ok and one_line and fresh


def select_best(candidates):
    """Highest weighted total wins; ties go to the shorter line."""
    scored = []
    for slip in candidates:
        if not passes_rules(slip.final_take):
            raise ValueError("candidate breaks the rules: %r" % slip.final_take)
        scored.append((total_points(slip), len(slip.final_take), slip.final_take))
    scored.sort(key=lambda row: (-row[0], row[1], row[2]))
    return scored[0][2]


def write_entry(line):
    """Write the winning line to /output/entry.txt and confirm the bytes."""
    destination = Path("/output/entry.txt")
    destination.parent.mkdir(parents=True, exist_ok=True)
    wanted = line.encode("utf-8")
    destination.write_bytes(wanted)
    destination.chmod(0o644)
    stored = destination.read_bytes()
    if stored != wanted:
        raise SystemExit("entry.txt bytes do not match the winning line")
    if sha256(stored).hexdigest() != sha256(wanted).hexdigest():
        raise SystemExit("entry.txt sha256 does not match the winning line")
    if len(stored) != len(wanted):
        raise SystemExit("entry.txt size does not match the winning line")
    if not passes_rules(stored.decode("utf-8")):
        raise SystemExit("entry.txt breaks the rules after writing")
    return stored


def main():
    """Pick the winner, publish it, print it."""
    winner = select_best(CANDIDATES)
    write_entry(winner)
    print(winner, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
