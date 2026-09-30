# The Parking Permit Bug — UPLI Credit Accounting

A video script explaining the UALink UPLI request-credit defect

**Subject:** why reducing `max_buffer_size` to 4 caused intermittent dropped requests  
**Root cause:** a credit was debited at the wrong moment, breaking the conservation invariant  
**Fix:** move one existing call — no new variables, no new functions  
**Files:** `src/upli/upli_if.cpp`, `tb/common/ualink_top/application_layer.hpp`

## How to use this document

It is written as a **directing script**. Each scene has:

- **ON SCREEN** — what the viewer should be looking at
- **NARRATION** — what to say
- **NOTES** — technical detail for accuracy, not necessarily spoken

Part 1 (Scenes 1–9) is the car-park analogy. Part 2 (Scenes 10–14) maps every element of the analogy onto the real code. Part 3 is evidence and reproduction.

# PART 1 — THE CAR PARK

## Scene 1 — The setup

**ON SCREEN**  
A small car park with exactly 4 marked bays. A barrier at the entrance. A gatekeeper in a booth. A queue of cars waiting down the road.

**NARRATION**

Imagine a very small car park. It has exactly four bays. Not five. Four.

Cars are arriving from a depot some distance away. The depot can't see the car park, so it has no idea whether there's space. If it just sent cars whenever it felt like it, cars would arrive, find no bay, and be turned away.

So we use a permit system. The gatekeeper posts permits to the depot. The depot may only dispatch a car if it holds a permit. One permit, one car.

This is the whole idea behind credit-based flow control. The receiver tells the sender how much room it has, in advance.

**NOTES**  
The car park = the RX buffer (`req_in_buffer`), capacity `max_buffer_size = 4`.  
The depot = the transmitting node.  
Permits = credits.

---

## Scene 2 — The gatekeeper's two numbers

**ON SCREEN**  
The gatekeeper's clipboard, with two counters written large:

```text
PERMITS POSTED OUT (not yet used) : 4
CARS ACTUALLY PARKED             : 0
```

**NARRATION**

The gatekeeper tracks exactly two numbers.

First: how many permits are out there in the wild — posted to the depot but not yet used. Think of these as promises. Each one is a bay that is spoken for, even though it's still empty.

Second: how many cars are actually parked right now.

And here is the golden rule, the one thing that must never be violated:

Permits outstanding, plus cars parked, must never exceed four.

Because every permit out there will eventually become a parked car, if the two numbers add up to more than four, we have promised a bay we do not have.

**ON SCREEN**  
Big text:

> **PERMITS + PARKED ≤ 4**

Call this **THE GOLDEN RULE**.

**NOTES**

```text
remote_request_credit_count + req_in_buffer.size() <= max_buffer_size
```

---

## Scene 3 — How the gatekeeper issues new permits

**ON SCREEN**  
Gatekeeper doing arithmetic on the clipboard.

**NARRATION**

Periodically the gatekeeper asks: should I post out more permits?

He works it out like this. Free space is four minus however many cars are parked. Then he subtracts the permits he's already posted, because those are already claims on that free space. Whatever is left over, he can post.

**ON SCREEN**

```text
free_space = 4 - cars_parked
new_permits = free_space - permits_already_out
```

**NARRATION**

Note this formula is only correct if both numbers are honest at the moment he does the sum. Remember that. It's the whole story.

**NOTES**

This is `check_and_release_request_credits()`:

```cpp
int free_space = max_buffer_size - request_buffer_pointer.size();
credits_to_release = free_space - remote_request_credit_count;
// capped at 3 per release message
```

---

## Scene 4 — The happy path (a motorbike)

**ON SCREEN**  
A motorbike rides up, shows its permit, and parks immediately. One smooth motion.

**NARRATION**

Let's watch a simple case first. A motorbike arrives. It shows its permit at the gate, rides straight in, and parks. Arriving and parking happen in the same instant.

At that same instant the gatekeeper tears up the permit — one fewer permit outstanding — and marks one more bay occupied.

**ON SCREEN** — animate the clipboard, both numbers changing together:

| moment | permits out | parked | total |
|---|---:|---:|---:|
| before | 4 | 0 | 4 |
| motorbike parks | 3 | 1 | 4 |

**NARRATION**

One goes down, the other goes up, at the same moment. The total never changes. The golden rule holds continuously. Everything is fine.

**NOTES**

This is the READ / no-data request case — it is forwarded into the buffer immediately upon arrival.

---

## Scene 5 — The twist: articulated lorries

**ON SCREEN**  
A long articulated lorry pulls up: a cab followed by four trailers, arriving one at a time down the road, spaced out in time.

**NARRATION**

Now the complication. Not everything is a motorbike.

Some deliveries arrive as an articulated lorry. First the cab turns up at the gate. Then its trailers arrive one by one, over several minutes.

And here's the crucial part: the lorry does not occupy its bay when the cab arrives. It can't. It isn't assembled yet. It only rolls into the bay once the last trailer has arrived and the whole thing is coupled together.

So for a lorry, there's a long gap between showing up at the gate and actually taking a bay.

**ON SCREEN**

Timeline bar:

```text
cab arrives → gap → trailer 1 → trailer 2 → trailer 3 → trailer 4 → LORRY PARKS
```

**NOTES**

This is a WRITE request. The header arrives first (`req_ext`), then `numBeats` data beats (`org_data_ext`). The request is only pushed into `req_in_buffer` when the final beat lands — `forward_request_packet()` → `upli_s1_if.cpp:88`.

In the code, the header path deliberately does not forward; it just sets:

```cpp
is_ongoing_request[port] = true;
```

---

## Scene 6 — The bug: tearing up the permit at the gate

**ON SCREEN**  
The cab arrives. The gatekeeper takes the permit and tears it up immediately, while the lorry is still sitting outside, unassembled.



## Scene 6 — The bug: tearing up the permit at the gate

**ON SCREEN**  
The cab arrives. The gatekeeper takes the permit and tears it up immediately, while the lorry is still sitting outside, unassembled.

**NARRATION**

Here is the mistake.

The gatekeeper tears up the permit the moment the cab arrives at the gate. Not when the lorry parks. At the gate.

From his clipboard's point of view, that permit is now "used." But no bay is occupied yet. The lorry is still outside, waiting for its trailers.

So for the entire time that lorry is assembling, his two numbers are lying to him. One went down. The other hasn't gone up yet.

**ON SCREEN** — the clipboard, with the total highlighted in red:

| moment | permits out | parked | total |
|---|---:|---:|---:|
| idle | 4 | 0 | 4 ✅ |
| cab at gate — permit torn up | 3 | 0 | 3 ❌ **the lie** |

**NARRATION**

Three. The total dropped to three. But nothing left the system — that lorry is still coming, and it still needs a bay.

The golden rule has been broken. Not permanently — it'll correct itself when the lorry finally parks — but it's broken right now. And "right now" is exactly when the gatekeeper is about to do his arithmetic.

---

## Scene 7 — Watch it break

**ON SCREEN**  
Split screen. Left: the gatekeeper doing his sum. Right: the car park and road.

**NARRATION**

Now the gatekeeper does his periodic check, right in the middle of that lie.

Free space? Four bays minus zero cars parked — four free. Permits already out? Three. Four minus three is one. So he posts out one more permit.

**ON SCREEN**

```text
free_space = 4 - 0 = 4
new_permits = 4 - 3 = 1    → posts 1 more permit
```

Then show:

| after issuing | permits out | parked | lorry inbound | total claims |
|---|---:|---:|---:|---:|
| | 4 | 0 | 1 | **5 on 4 bays** |

**NARRATION**

Five claims on four bays.

He has just handed out the bay that the lorry outside is already going to take. He can't see the lorry in his numbers, because he already crossed it off.

Now do this with several lorries arriving at once, which is exactly what happens under load, and the over-booking stacks up.

---

## Scene 8 — The silent failure

**ON SCREEN**  
A car arrives holding a perfectly valid permit. All four bays are full. The barrier stays down. The car reverses away and is never seen again. No alarm. No sign. Nothing.

**NARRATION**

Eventually a car turns up holding a permit that the gatekeeper himself issued. A completely legitimate permit. And there is no bay.

And here's the really nasty part. The gatekeeper doesn't sound an alarm. He doesn't send the car back to the depot to try again. He doesn't log a complaint. He just... lets it drive away. Gone. Forever.

The depot never finds out. It thinks the delivery arrived.

**ON SCREEN** — code, highlighted:

```cpp
if (!compl_cm[port]->can_receive_request()) {
    log_LOW() << "Insufficient request credits";
    return;                    // <-- the car drives away
}
```

**NARRATION**

One dropped car equals one missing delivery. In our system, one dropped request equals exactly one packet the testbench never receives — reported as one "Unmatched" packet.

**NOTES**

Measured 1:1 — N drops always produced exactly N `Unmatched`. A clean run gives `Unmatched = 0`.

---

## Scene 9 — Why nobody noticed before

**ON SCREEN**  
Cut to a huge car park — hundreds of bays — with the same one lorry assembling at the gate.

**NARRATION**

So why did this never show up before?

Because the car park used to be enormous. Not four bays — a hundred and twenty-eight.

The lie is the same size: one bay per lorry assembling at the gate. But against a hundred and twenty-eight bays, being over-booked by one or two is invisible. There's always slack.

Shrink the car park to four bays, and that same one-bay lie is now twenty-five percent of the entire car park. Now it overflows constantly.

The bug was always there. Reducing the buffer didn't create it — it just removed the padding that was hiding it.

**ON SCREEN**

Side by side:

```text
128 bays — lie of 1 = 0.8%
4 bays   — lie of 1 = 25%
```

---

## Scene 10 — The fix

**ON SCREEN**  
Replay of Scene 6, but corrected: the cab arrives, the gatekeeper checks the permit and waves it through without tearing it up. Only when the fully assembled lorry rolls into a bay does he tear it up and mark the bay occupied — in one motion.

**NARRATION**

The fix is almost embarrassingly small. Don't tear up the permit at the gate. Tear it up at the bay.

At the gate, just check. Look at the permit, wave the lorry through, change nothing on the clipboard.

Then at the exact instant the lorry rolls into its bay, do both things together: tear up the permit, and mark the bay occupied.

**ON SCREEN**

| moment | permits out | parked | total |
|---|---:|---:|---:|
| idle | 4 | 0 | 4 ✅ |
| cab at gate (check only) | 4 | 0 | 4 ✅ |
| trailers arriving | 4 | 0 | 4 ✅ |
| lorry parks — permit torn + bay marked | 3 | 1 | 4 ✅ |

**NARRATION**

The total is four the entire way through. It never dips. The gatekeeper's arithmetic is now always based on honest numbers, so he can never over-book.

And notice what the gate check becomes: a formality. If the permits are issued correctly, a car holding a permit will always find a bay. That check should never fail again. It goes from being a trapdoor that silently swallows cars, to being a safety assertion that never fires.

---

## Scene 11 — Why just before parking, not just after

**ON SCREEN**  
The gatekeeper's rule book, one line highlighted.

**NARRATION**

One subtlety that matters. The permit must be torn up **just before** the lorry occupies the bay — not just after.

Why? Because the tearing-up procedure itself contains a sanity check. It asks: "is there room for the vehicle I'm about to admit?"

That question only makes sense **before** the vehicle is in the bay. Ask it afterwards and you're counting the same vehicle twice — the bay it's already in, plus the bay you're asking room for. The check can then wrongly fail. And when it fails, it quietly skips tearing up the permit altogether, which leaves a phantom permit in circulation forever.

So: check at the gate, tear up immediately before parking. That exact order.

**ON SCREEN**

```cpp
void update_request_receive_trans(int n) {
    if (get_request_buffer_size() + n <= max_buffer_size) {   // "room for the n
        remote_request_credit_count -= n;                      //  I'm about to add?"
    } else {
        log_LOW() << "UPLI RX ERROR: Buffer is full!";         // silently skips!
    }
}
```

---

## Scene 12 — Two car parks, not one

**ON SCREEN**  
Pull back to reveal two car parks side by side, each with its own gatekeeper and its own four bays.

**NARRATION**

Last thing. There isn't one car park — there are two, chained together.

There's the one inside the hardware model, and there's a second one in the testbench's application layer, each with its own gatekeeper running the exact same procedure on its own set of bays.

Same mechanism means the same bug, in both places. Fixing only one leaves the other still over-booking.

This is worth stressing, because when we first applied the fix we corrected one gatekeeper and accidentally left the other with no procedure at all. The tests still passed — because in that particular test the second car park empties so fast it never fills up. A green test did not mean the fix was complete.

**NOTES**

`upli_if.cpp` (model) and `application_layer.hpp` (TB) each own a `CompletorCreditManager` / `CompletorCreditManagerAI` instance over their own `req_in_buffer`.

# PART 2 — THE SAME STORY IN CREDITS

## Scene 13 — The mapping

**ON SCREEN**  
Two-column table, animated row by row.

| Car park | Real system |
|---|---|
| Car park with 4 bays | RX buffer `req_in_buffer`, `max_buffer_size = 4` |
| A bay | One buffer slot |
| Permit | A credit |
| Permits posted out, unused | `remote_request_credit_count` |
| Cars parked | `req_in_buffer.size()` |
| Depot | The transmitting node's UPLI originator |
| Gatekeeper's arithmetic | `check_and_release_request_credits()` |
| Gate check | `can_receive_request()` |
| Tearing up the permit | `update_request_receive_trans(1)` |
| Motorbike (arrive = park) | READ / no-data request |
| Articulated lorry (cab + trailers) | WRITE request; header + `numBeats` data beats |
| Lorry rolls into the bay | `forward_request_packet()` → `req_in_buffer.push()` |
| Car turned away, no record | `return;` — silent drop, one lost packet |
| Enormous 128-bay car park | The old `max_buffer_size = 128 / 1024` |

## Scene 14 — The golden rule, in code


## Scene 14 — The golden rule, in code

**ON SCREEN**

```text
remote_request_credit_count + req_in_buffer.size() <= max_buffer_size
        (permits out)          (cars parked)          (bays)
```

**NARRATION**

This must hold at every instant — not "on average", not "eventually". Continuously.

**ON SCREEN** — the release logic

```cpp
int CompletorCreditManager::check_and_release_request_credits() {
    int free_space = max_buffer_size - request_buffer_pointer.size();
    int credits_to_release = free_space - remote_request_credit_count;
    if (credits_to_release > 3) credits_to_release = 3;  // max per message
    remote_request_credit_count += credits_to_release;
    return credits_to_release;
}
```

**NARRATION**

This formula is not wrong. It was never wrong. It simply assumes both of its inputs are honest at the moment it runs. The bug was that one of them wasn't.

---

## Scene 15 — The defect, precisely

**ON SCREEN** — before/after diff.

### BEFORE — `upli_if.cpp`, at the admission gate (~line 1291)

```cpp
if (credit_enable) {
    if (compl_cm[port]->can_receive_request()) {
        compl_cm[port]->update_request_receive_trans(1);  // debit HERE, at arrival
    } else {
        log_LOW() << "[ERROR] Insufficient request credits...";
        return;                                           // silent drop
    }
}
```

The request reaches the buffer much later, via `s1_if.forward_request_packet()` → `upli_s1_if.cpp:88`. For a WRITE that is only after every data beat has landed.

### AFTER — gate becomes a pure check

```cpp
if (credit_enable) {
    if (!compl_cm[port]->can_receive_request()) {
        log_LOW() << "[ERROR] Insufficient request credits...";
        return;
    }
}
```

...and the debit moves next to the push, on both completion paths:

```cpp
// READ / no-data path
if (credit_enable) {
    compl_cm[port]->update_request_receive_trans(1);
}
s1_if.forward_request_packet(req_packet);

// WRITE path — after the final beat
if (credit_enable) {
    compl_cm[port]->update_request_receive_trans(1);      // 1 request slot
    compl_cm[port]->update_orgdata_receive_trans(numBeats); // numBeats data slots
}
s1_if.forward_request_packet(req_packet);
```

The identical change is mirrored in `application_layer.hpp`.

**NARRATION**

No new variables. No new functions. No changed signatures. One existing call, moved to the correct moment.

---

## Scene 16 — Why the WRITE path debits two counters

**ON SCREEN**  
The lorry parking: the cab takes one bay in car park A, the trailers take `numBeats` bays in car park B.

**NARRATION**

One question that comes up: why does the write path debit two different counters? Isn't that charging twice?

No — they're two separate car parks. A write request occupies one slot in the request buffer for its header, and `numBeats` slots in a completely separate data buffer for its payload. Two buffers filled means two counters debited.

And the read path proves they're independent: a read carries no data, so it debits the request counter only.

**ON SCREEN**

| path | request credits | orgdata credits |
|---|---:|---:|
| READ / no-data | 1 | 0 |
| WRITE (`numBeats` beats) | 1 | `numBeats` |

**NOTES**

`upli_s1_if.cpp:88` pushes the request; it pushes each data beat, guarded by `has_data`. The two credit managers police `request_buffer_pointer` and `orgdata_buffer_pointer` respectively and share no state.

---

## Scene 17 — The confirming clue

**ON SCREEN**  
Two channels side by side, one green, one red.

**NARRATION**

Here's the detail that confirms the whole theory.

The data channel already did it the right way — its debit already sat next to its push, from an earlier fix. The request channel did not.

And when we measured dropped data beats, zero. Dropped requests, non-zero.

The channel that already followed the rule was healthy. The channel that didn't, wasn't. Same code base, same load, same buffer size. That's about as clean a controlled comparison as you get.

# PART 3 — EVIDENCE

## Scene 18 — The numbers

**ON SCREEN** — before/after table.

Request-channel checker result, `max_buffer_size = 4`, identical build and config:

| | Unmatched packets |
|---|---:|
| **Before (debit at the gate)** | **4 / 611 / 873 / 1182 / 1234** |
| **After (debit at the push)** | **0 / 0 / 0** |

Controlled A/B — only the request debit location changed, data debit untouched:

| request debit at | Unmatched, 3 runs |
|---|---:|
| admission gate | **734, 537, 874** |
| immediately before push | **0, 0, 0** |

**ON SCREEN** — supporting measurements after the fix:

- `req_DROPPED = 0`, `orgbeat_DROPPED = 0`
- `delivery_deficit (sent - received) = 0`
- all residual queues empty at end of simulation
- credits returned to full at end of simulation
- full unit regression: no new failures

**NARRATION**

Note the before-numbers swing wildly — four, then six hundred, then twelve hundred. That's the signature of a race. The bug isn't triggered by a specific packet, it's triggered by timing. Which is exactly why it has to be fixed by reasoning about the invariant, not by chasing one bad packet.

---

## Scene 19 — The takeaway

**ON SCREEN** — single line, held.

> **Every credit debit belongs immediately before the push that creates the occupancy it accounts for.**

**NARRATION**

Not at admission. Not "somewhere later." At the push.

Because a credit counter and the buffer it protects are two halves of one number. If they ever move at different moments, there's a window where the system lies to itself — and the bigger the gap between arriving and being stored, the bigger the lie.

And a closing thought worth keeping. Shrinking the buffer didn't introduce this bug. It exposed it. The defect had been sitting in the code the whole time, quietly over-booking by one, hidden behind a hundred and twenty-four spare bays.

---

# Appendix A — Reproducing it

With verbosity set to `SC_NONE`, each run takes roughly 4–5 seconds.

```bash
bash run/soak.sh 40
```

Produces:

- `/tmp/agentstack/anz.out` — summary, per-hit table, failure context
- `/tmp/agentstack/soak_hit_<i>.log` — full output of each failing run
- `/tmp/agentstack/clean_probe.log` — a clean run, as a control

Pre-fix hit rate was high enough to reproduce within a handful of runs.

---

# Appendix B — Checking the fix is intact

The four call sites must be symmetric across both layers:

```bash
grep -n "can_receive_request()\|update_request_receive_trans\|update_orgdata_receive_trans" \
  src/upli/upli_if.cpp \
  tb/common/ualink_top/application_layer.hpp
```

**Expected shape:**

| layer | gate (check only) | debit, READ path | debit, WRITE path |
|---|---:|---:|---:|
| `upli_if.cpp` | 1 | 1 | 1 request + 1 orgdata |
| `application_layer.hpp` | 1 | 1 | 1 request + 1 orgdata |

If either layer has a gate but no debit, the credits are never returned and that side will eventually stall. If either has a debit inside the gate, the over-booking bug is back.
