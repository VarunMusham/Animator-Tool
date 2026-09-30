"""Narration beats for Part 1 (scenes 1-3). One beat = one sentence group = one visual step.
Text is taken verbatim from script/parking_permit_credit_bug.md, only split at sentence boundaries."""

VOICE = "en-GB-RyanNeural"
RATE = "+8%"

SCENES = [
    dict(id="s1", chip="SCENE 1  ·  THE SETUP", beats=[
        "Imagine a very small car park. It has exactly four bays. Not five. Four.",
        "Cars are arriving from a depot some distance away. The depot can't see the car park, so it has no idea whether there's space.",
        "If it just sent cars whenever it felt like it, cars would arrive, find no bay, and be turned away.",
        "So we use a permit system. The gatekeeper posts permits to the depot.",
        "The depot may only dispatch a car if it holds a permit. One permit, one car.",
        "This is the whole idea behind credit-based flow control. The receiver tells the sender how much room it has, in advance.",
    ]),
    dict(id="s2", chip="SCENE 2  ·  THE GATEKEEPER'S TWO NUMBERS", beats=[
        "The gatekeeper tracks exactly two numbers.",
        "First: how many permits are out there in the wild — posted to the depot but not yet used.",
        "Think of these as promises. Each one is a bay that is spoken for, even though it's still empty.",
        "Second: how many cars are actually parked right now.",
        "And here is the golden rule, the one thing that must never be violated:",
        "Permits outstanding, plus cars parked, must never exceed four.",
        "Because every permit out there will eventually become a parked car, if the two numbers add up to more than four, we have promised a bay we do not have.",
    ]),
    dict(id="s3", chip="SCENE 3  ·  HOW THE GATEKEEPER ISSUES NEW PERMITS", beats=[
        "Periodically the gatekeeper asks: should I post out more permits?",
        "He works it out like this. Free space is four minus however many cars are parked.",
        "Then he subtracts the permits he's already posted, because those are already claims on that free space.",
        "Whatever is left over, he can post.",
        "Note this formula is only correct if both numbers are honest at the moment he does the sum.",
        "Remember that. It's the whole story.",
    ]),
    dict(id="s4", chip="SCENE 4  ·  THE HAPPY PATH (A MOTORBIKE)", beats=[
        "Let's watch a simple case first. A motorbike arrives.",
        "It shows its permit at the gate, rides straight in, and parks. Arriving and parking happen in the same instant.",
        "At that same instant the gatekeeper tears up the permit — one fewer permit outstanding — and marks one more bay occupied.",
        "One goes down, the other goes up, at the same moment.",
        "The total never changes. The golden rule holds continuously. Everything is fine.",
    ]),
    dict(id="s5", chip="SCENE 5  ·  THE TWIST: ARTICULATED LORRIES", beats=[
        "Now the complication. Not everything is a motorbike.",
        "Some deliveries arrive as an articulated lorry.",
        "First the cab turns up at the gate.",
        "Then its trailers arrive one by one, over several minutes.",
        "And here's the crucial part: the lorry does not occupy its bay when the cab arrives. It can't. It isn't assembled yet.",
        "It only rolls into the bay once the last trailer has arrived and the whole thing is coupled together.",
        "So for a lorry, there's a long gap between showing up at the gate and actually taking a bay.",
    ]),
    dict(id="s6", chip="SCENE 6  ·  THE BUG: TEARING UP THE PERMIT AT THE GATE", beats=[
        "Here is the mistake.",
        "The gatekeeper tears up the permit the moment the cab arrives at the gate. Not when the lorry parks. At the gate.",
        "From his clipboard's point of view, that permit is now \"used.\" But no bay is occupied yet. The lorry is still outside, waiting for its trailers.",
        "So for the entire time that lorry is assembling, his two numbers are lying to him. One went down. The other hasn't gone up yet.",
        "Three. The total dropped to three. But nothing left the system — that lorry is still coming, and it still needs a bay.",
        "The golden rule has been broken. Not permanently — it'll correct itself when the lorry finally parks — but it's broken right now.",
        "And \"right now\" is exactly when the gatekeeper is about to do his arithmetic.",
    ]),
    dict(id="s7", chip="SCENE 7  ·  WATCH IT BREAK", beats=[
        "Now the gatekeeper does his periodic check, right in the middle of that lie.",
        "Free space? Four bays minus zero cars parked — four free.",
        "Permits already out? Three. Four minus three is one. So he posts out one more permit.",
        "Five claims on four bays.",
        "He has just handed out the bay that the lorry outside is already going to take. He can't see the lorry in his numbers, because he already crossed it off.",
        "Now do this with several lorries arriving at once, which is exactly what happens under load, and the over-booking stacks up.",
    ]),
    dict(id="s8", chip="SCENE 8  ·  THE SILENT FAILURE", beats=[
        "Eventually a car turns up holding a permit that the gatekeeper himself issued. A completely legitimate permit. And there is no bay.",
        "And here's the really nasty part. The gatekeeper doesn't sound an alarm.",
        "He doesn't send the car back to the depot to try again. He doesn't log a complaint.",
        "He just... lets it drive away. Gone. Forever.",
        "The depot never finds out. It thinks the delivery arrived.",
        "One dropped car equals one missing delivery. In our system, one dropped request equals exactly one packet the testbench never receives — reported as one \"Unmatched\" packet.",
    ]),
    dict(id="s9", chip="SCENE 9  ·  WHY NOBODY NOTICED BEFORE", beats=[
        "So why did this never show up before?",
        "Because the car park used to be enormous. Not four bays — a hundred and twenty-eight.",
        "The lie is the same size: one bay per lorry assembling at the gate. But against a hundred and twenty-eight bays, being over-booked by one or two is invisible. There's always slack.",
        "Shrink the car park to four bays, and that same one-bay lie is now twenty-five percent of the entire car park. Now it overflows constantly.",
        "The bug was always there. Reducing the buffer didn't create it — it just removed the padding that was hiding it.",
    ]),
]
