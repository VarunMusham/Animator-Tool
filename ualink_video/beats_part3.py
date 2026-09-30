"""Narration beats for Part 3 (scenes 18-19 + appendices A and B).
Scenes 18 (last beat) and 19 (beats 1-3) are verbatim from script/parking_permit_credit_bug.md. The remaining beats narrate
on-screen material that the script leaves silent (the numbers, the takeaway line itself, and both appendices)."""

TITLE = dict(title="The Evidence", sub="The numbers, the takeaway, and how to reproduce it",
             tag="Part 3  ·  Scenes 18–19 and appendices")

SCENES = [
    dict(id="s18", chip="SCENE 18  ·  THE NUMBERS", beats=[
        "Here are the numbers. On the request-channel checker, with the buffer size set to four, the unmatched packet count before the fix was four, six hundred and eleven, eight hundred and seventy-three, eleven hundred and eighty-two, and twelve hundred and thirty-four. After the fix: zero, zero, zero.",
        "A controlled A B comparison changes only where the request debit sits, and leaves the data debit untouched. With the debit at the admission gate: seven hundred and thirty-four, five hundred and thirty-seven, and eight hundred and seventy-four unmatched. Immediately before the push: zero, zero, zero.",
        "After the fix, dropped requests and dropped data beats are both zero, nothing is missing between sent and received, every residual queue is empty, credits return to full, and the full unit regression shows no new failures.",
        "Note the before-numbers swing wildly — four, then six hundred, then twelve hundred. That's the signature of a race.",
        "The bug isn't triggered by a specific packet, it's triggered by timing. Which is exactly why it has to be fixed by reasoning about the invariant, not by chasing one bad packet.",
    ]),
    dict(id="s19", chip="SCENE 19  ·  THE TAKEAWAY", beats=[
        "Every credit debit belongs immediately before the push that creates the occupancy it accounts for.",
        "Not at admission. Not \"somewhere later.\" At the push.",
        "Because a credit counter and the buffer it protects are two halves of one number. If they ever move at different moments, there's a window where the system lies to itself — and the bigger the gap between arriving and being stored, the bigger the lie.",
        "And a closing thought worth keeping. Shrinking the buffer didn't introduce this bug. It exposed it. The defect had been sitting in the code the whole time, quietly over-booking by one, hidden behind a hundred and twenty-four spare bays.",
    ]),
    dict(id="s20", chip="APPENDIX A  ·  REPRODUCING IT", beats=[
        "To reproduce it, run the soak script with forty iterations. With verbosity set to S C none, each run takes roughly four to five seconds.",
        "It produces three things: a summary with a per-hit table and the failure context, the full output of every failing run, and a clean run kept as a control.",
        "Before the fix, the hit rate was high enough to reproduce the bug within a handful of runs.",
    ]),
    dict(id="s21", chip="APPENDIX B  ·  CHECKING THE FIX IS INTACT", beats=[
        "To check the fix is intact, grep for the three credit calls across both files.",
        "The call sites must be symmetric across both layers: one gate check, one debit on the read path, and on the write path one request debit plus one data debit.",
        "If either layer has a gate but no debit, the credits are never returned, and that side will eventually stall.",
        "And if either has a debit inside the gate, the over-booking bug is back.",
    ]),
]
