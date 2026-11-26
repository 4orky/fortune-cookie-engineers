#!/usr/bin/env python3
# Fortune cookie foundry for software engineers — make.fun bounty
# u-eager-stork-81-9647-fortune-cookie-funnies-for-866bde2a
#
# The program writes one fortune cookie message aimed at a software
# engineer (a single line of at most 120 characters) to
# /output/entry.txt. Twelve lines were drafted by hand against the
# judge's brief, in order of weight:
#   1. reads as a real fortune cookie message for a software engineer,
#      in the voice of a fortune slip ("You will...", "Beware...",
#      "Lucky numbers..."), not a general slogan
#   2. funny on first read, with a turn or a surprise rather than a
#      plain statement
#   3. speaks to an engineer's own condition — deploys, bugs, code
#      review, branches, on-call — in a way that earns the joke
#   4. fresh: no stock joke from a mug or a conference slide (no
#      "works on my machine", no "99 bugs", no "not a bug, a feature")
#   5. one crisp line a cookie could hold, no wasted words
# Each entry keeps its first draft, its revised final, a note on what
# the revision fixed, and marks out of ten per lens. Selection is
# deterministic: highest weighted total wins, and a tie goes to the
# shorter line. The output is byte-identical on every run.
from hashlib import md5 as _md5
from hashlib import sha256 as _sha256
from pathlib import Path as _Path
_WEIGHTS = {"fortune": 3, "impact": 3, "engineer": 2, "freshness": 2, "economy": 1}
_FORBIDDEN = ("works on my machine", "not a bug", "10 kinds of people",
              "turn it off and on", "99 little bugs", "have you tried turning")
_ENTRIES = [
    {"draft": "Your next deploy will succeed on the first try, and nobody will believe it \u2014 least of all you.",
     "final": "Your next deploy will succeed on the first try. Nobody will believe you, least of all you.",
     "polish": "Split one flat sentence into two so the second lands as its own punch, and changed 'believe it' to 'believe you' so the disbelief is personal, not about the deploy.",
     "marks": {"fortune": 10, "impact": 9, "engineer": 9, "freshness": 9, "economy": 9}},
    {"draft": "The bug you fear most has already been fixed, in a branch nobody ever merged.",
     "final": "The bug you fear most is already fixed \u2014 in a branch nobody merged.",
     "polish": "Tightened 'has already been fixed' to 'is already fixed', cut 'ever', and let the em dash carry the beat so the twist arrives in one breath.",
     "marks": {"fortune": 8, "impact": 9, "engineer": 10, "freshness": 10, "economy": 10}},
    {"draft": "A stranger will fix your bug in review, and you will spend the afternoon pretending you saw it too.",
     "final": "A stranger will fix your bug in review. You will spend the afternoon pretending you saw it too.",
     "polish": "Cut the comma splice into two sentences so the confession in the second half stands on its own.",
     "marks": {"fortune": 7, "impact": 8, "engineer": 10, "freshness": 9, "economy": 8}},
    {"draft": "A wise engineer deletes code, and a wiser one deletes the meeting about deleting the code.",
     "final": "A wise engineer deletes code. A wiser one deletes the meeting about deleting the code.",
     "polish": "Broke the sentence at the period so the second clause reads as the proverb's own punchline instead of an afterthought.",
     "marks": {"fortune": 7, "impact": 8, "engineer": 9, "freshness": 9, "economy": 9}},
    {"draft": "Lucky numbers: 0, 1, and the build number you stopped checking a few deploys ago.",
     "final": "Lucky numbers: 0, 1, and the build number you stopped checking three deploys ago.",
     "polish": "Swapped the vague 'a few' for the exact 'three': a fortune slip deals in specifics, and the number makes the neglect concrete.",
     "marks": {"fortune": 10, "impact": 7, "engineer": 8, "freshness": 7, "economy": 8}},
    {"draft": "Your code will outlive you, and unfortunately so will the comment explaining why it cannot be changed.",
     "final": "Your code will outlive you. Unfortunately, so will the comment explaining why it cannot be changed.",
     "polish": "Split the sentence so 'Unfortunately' opens the second half and the joke lands on the comment, not on the code.",
     "marks": {"fortune": 8, "impact": 8, "engineer": 9, "freshness": 7, "economy": 8}},
    {"draft": "The bug is not in your code, it is in the code you copied and trusted and never read.",
     "final": "The bug is not in your code. It is in the code you copied, trusted, and never read.",
     "polish": "Period instead of a comma, and commas in the triplet, so the three verbs land as a charge sheet against the reader.",
     "marks": {"fortune": 7, "impact": 8, "engineer": 9, "freshness": 8, "economy": 9}},
    {"draft": "Your pull request will be approved by the one reviewer who never reads code, so cherish this rare alignment.",
     "final": "Your pull request will be approved by the one reviewer who never reads code. Cherish this rare alignment.",
     "polish": "Cut 'so' and made the last three words a command: the fortune now blesses the luck instead of merely describing it.",
     "marks": {"fortune": 6, "impact": 8, "engineer": 10, "freshness": 9, "economy": 8}},
    {"draft": "Beware the engineer who says 'just one more refactor', because your weekend is already in his commit history.",
     "final": "Beware the engineer who says \u2018just one more refactor\u2019 \u2014 your weekend is already in his commit history.",
     "polish": "Replaced the explaining 'because' with an em dash and straight quotes with curly ones, so the warning sounds like a printed slip, not a lecture.",
     "marks": {"fortune": 8, "impact": 7, "engineer": 9, "freshness": 7, "economy": 8}},
    {"draft": "You will inherit a codebase with no tests and one comment, 'good luck', and it is the truest fortune ever written.",
     "final": "You will inherit a codebase with no tests and one comment: \u2018good luck.\u2019 It is the truest fortune ever written.",
     "polish": "The colon makes the comment a quotation on the slip itself, and the full stop inside the quotes closes the previous owner's message.",
     "marks": {"fortune": 7, "impact": 8, "engineer": 9, "freshness": 7, "economy": 8}},
    {"draft": "The feature you shipped at midnight will be loved by everyone except the person who has to maintain it, future you.",
     "final": "The feature you shipped at midnight will be loved by everyone except the person who maintains it: future you.",
     "polish": "Cut 'has to' and let a colon introduce 'future you', so the identity reveal is the last thing the reader meets.",
     "marks": {"fortune": 7, "impact": 7, "engineer": 9, "freshness": 7, "economy": 7}},
    {"draft": "You will find the bug in the last place you look, the code you wrote yesterday and swore was perfect.",
     "final": "You will find the bug in the last place you look: the code you wrote yesterday and swore was perfect.",
     "polish": "A colon instead of a comma turns the second half into the reveal the first half is pointing at.",
     "marks": {"fortune": 8, "impact": 6, "engineer": 8, "freshness": 6, "economy": 7}},
]  # twelve drafts scored; the first entry wins on weighted total
def _weighted(marks):
    return sum(marks[lens] * _WEIGHTS[lens] for lens in _WEIGHTS)
def _acceptable(line):
    stripped = line.strip()
    if not 1 <= len(stripped) <= 120:
        return False
    if "\n" in stripped or "\r" in stripped:
        return False
    lowered = stripped.lower()
    return not any(phrase in lowered for phrase in _FORBIDDEN)
def _choose(entries):
    ranked = []
    for entry in entries:
        line = entry["final"]
        if not _acceptable(line):
            raise ValueError("entry fails the gate: %r" % line)
        ranked.append((_weighted(entry["marks"]), -len(line), line))
    ranked.sort(reverse=True)
    return ranked[0][2]
def _publish(line):
    target = _Path("/output/entry.txt")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(line, encoding="utf-8")
    target.chmod(0o644)
    raw = target.read_bytes()
    if _sha256(raw).hexdigest() != _sha256(line.encode("utf-8")).hexdigest():
        raise SystemExit("entry.txt bytes differ from the chosen line")
    if _md5(raw).hexdigest() != _md5(line.encode("utf-8")).hexdigest():
        raise SystemExit("entry.txt md5 differs from the chosen line")
    import stat as _stat
    if _stat.S_IMODE(target.stat().st_mode) != 0o644:
        raise SystemExit("entry.txt is not world-readable")
    checked = raw.decode("utf-8")
    if not _acceptable(checked):
        raise SystemExit("entry.txt fails the gate after writing")
    print(line, flush=True)
if __name__ == "__main__": _publish(_choose(_ENTRIES))
