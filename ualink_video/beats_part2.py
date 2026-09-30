"""Narration beats for Part 2 (scenes 10-17). Text is verbatim from script/parking_permit_credit_bug.md, split at sentence
boundaries. A beat is either a string (narrated) or dict(silent=<seconds>, cap=<caption>) for on-screen-only beats."""

TITLE = dict(title="Same Story, in Code", sub="The fix, and where it lives in the UPLI credit logic",
             tag="Part 2  ·  Scenes 10–17")

SCENES = [
    dict(id="s10", chip="SCENE 10  ·  THE FIX", beats=[
        "The fix is almost embarrassingly small. Don't tear up the permit at the gate. Tear it up at the bay.",
        "At the gate, just check. Look at the permit, wave the lorry through, change nothing on the clipboard.",
        "Then at the exact instant the lorry rolls into its bay, do both things together: tear up the permit, and mark the bay occupied.",
        "The total is four the entire way through. It never dips. The gatekeeper's arithmetic is now always based on honest numbers, so he can never over-book.",
        "And notice what the gate check becomes: a formality. If the permits are issued correctly, a car holding a permit will always find a bay. That check should never fail again.",
        "It goes from being a trapdoor that silently swallows cars, to being a safety assertion that never fires.",
    ]),
    dict(id="s11", chip="SCENE 11  ·  WHY JUST BEFORE PARKING, NOT JUST AFTER", beats=[
        "One subtlety that matters. The permit must be torn up just before the lorry occupies the bay — not just after.",
        "Why? Because the tearing-up procedure itself contains a sanity check. It asks: \"is there room for the vehicle I'm about to admit?\"",
        "That question only makes sense before the vehicle is in the bay. Ask it afterwards and you're counting the same vehicle twice — the bay it's already in, plus the bay you're asking room for.",
        "The check can then wrongly fail. And when it fails, it quietly skips tearing up the permit altogether, which leaves a phantom permit in circulation forever.",
        "So: check at the gate, tear up immediately before parking. That exact order.",
    ]),
    dict(id="s12", chip="SCENE 12  ·  TWO CAR PARKS, NOT ONE", beats=[
        "Last thing. There isn't one car park — there are two, chained together.",
        "There's the one inside the hardware model, and there's a second one in the testbench's application layer, each with its own gatekeeper running the exact same procedure on its own set of bays.",
        "Same mechanism means the same bug, in both places. Fixing only one leaves the other still over-booking.",
        "This is worth stressing, because when we first applied the fix we corrected one gatekeeper and accidentally left the other with no procedure at all.",
        "The tests still passed — because in that particular test the second car park empties so fast it never fills up. A green test did not mean the fix was complete.",
    ]),
    dict(id="s13", chip="SCENE 13  ·  THE MAPPING", beats=[
        "Now let's map every part of the car park onto the real code.",
        "The car park is the receive buffer, req in buffer, with a capacity of four. Each bay is one buffer slot, and each permit is a credit.",
        "Permits posted out but not yet used are the remote request credit count. Cars parked is the size of req in buffer. And the depot is the transmitting node's UPLI originator.",
        "The gatekeeper's arithmetic is check and release request credits. The gate check is can receive request. Tearing up the permit is update request receive trans.",
        "A motorbike is a read, or any request with no data. The articulated lorry is a write: a header, plus num beats data beats.",
        "The lorry rolling into its bay is forward request packet pushing into req in buffer. And a car turned away with no record is that silent return, one lost packet.",
        "Finally, the enormous car park is the old buffer size: a hundred and twenty-eight, or a thousand and twenty-four.",
    ]),
    dict(id="s14", chip="SCENE 14  ·  THE GOLDEN RULE, IN CODE", beats=[
        "This must hold at every instant — not \"on average\", not \"eventually\".",
        "Continuously.",
        "This formula is not wrong. It was never wrong.",
        "It simply assumes both of its inputs are honest at the moment it runs.",
        "The bug was that one of them wasn't.",
    ]),
    dict(id="s15", chip="SCENE 15  ·  THE DEFECT, PRECISELY", beats=[
        "At the admission gate, the debit happened the moment a request arrived. But the request only reaches the buffer much later — for a write, only after every data beat has landed.",
        "The fix makes the gate a pure check. It looks, and changes nothing.",
        "And the debit moves to sit right next to the push, on both paths. A read debits one request slot. A write debits one request slot, plus one data slot for every beat. The identical change is mirrored in the testbench's application layer.",
        "No new variables. No new functions. No changed signatures. One existing call, moved to the correct moment.",
    ]),
    dict(id="s16", chip="SCENE 16  ·  WHY THE WRITE PATH DEBITS TWO COUNTERS", beats=[
        "One question that comes up: why does the write path debit two different counters? Isn't that charging twice?",
        "No — they're two separate car parks.",
        "A write request occupies one slot in the request buffer for its header, and numBeats slots in a completely separate data buffer for its payload. Two buffers filled means two counters debited.",
        "And the read path proves they're independent: a read carries no data, so it debits the request counter only.",
    ]),
    dict(id="s17", chip="SCENE 17  ·  THE CONFIRMING CLUE", beats=[
        "Here's the detail that confirms the whole theory.",
        "The data channel already did it the right way — its debit already sat next to its push, from an earlier fix. The request channel did not.",
        "And when we measured dropped data beats, zero. Dropped requests, non-zero.",
        "The channel that already followed the rule was healthy. The channel that didn't, wasn't. Same code base, same load, same buffer size. That's about as clean a controlled comparison as you get.",
    ]),
]
