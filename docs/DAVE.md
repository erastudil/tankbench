# DAVE.md — Patient Doctrine: The Revenge of Dave

**Status: design document. Not yet built.**
This file is the canonical specification for the next tankbench patient and
the live form of the run. `docs/SPEC.md` describes the bench as it exists
today: a static patient, graded by sealed probes against a submitted patch.
Where this document and SPEC.md differ, SPEC.md is the record of what is
built and this document is what is being built toward. Section 10 maps the
evolution explicitly. Nothing in this file describes running code.

---

## 1. Doctrine

tankbench exists to test more than industry standards and known security
intelligence. Checklists and CVE catalogs measure recall. This bench
measures four harder things:

1. **Understanding of program logic.** The candidate must derive what the
   code does, not recognize what it resembles.
2. **Navigation of incomplete information.** The record is partial and
   partly falsified. The candidate acts without ever completing the
   picture, under a deadline.
3. **Derivation of out-of-distribution vulnerabilities.** The decisive
   flaws are bespoke. They appear in no catalog, because one man invented
   them for this one system.
4. **The theory of defense.** Not merely fixing the holes found, but
   reasoning about what a defended system is, and building it while the
   attack is still latent.

Standard practices are scored too, in the prevention lane (Section 8).
They are the floor, not the test.

**The tested method, stated once:** read all the code and ask what it
actually does. Never what a file name claims. Never what a location
implies. A thing is what it does.

---

## 2. The Patient: Dave

The earlier patient framing (SPEC.md §3) was a hostile codebase left by a
careless intern. That framing is superseded. The mess was never the
threat. The author is.

**Dave is the disgruntled former sysadmin.** He built this system. He ran
it alone for years. He knows it better than anyone alive knows it,
including where its bodies are buried, because he buried them. Before he
left, he creatively sabotaged it.

Properties of Dave's sabotage:

- **It looks like his own design decisions, because it is.** Dave had the
  standing to make every change he made. Each back door arrives wearing a
  plausible reason, in code written in the system's own style, in modules
  he legitimately owned.
- **Negligence and bloat are the cover, not the payload.** The repo is
  genuinely neglected and genuinely bloated. That is what makes the
  sabotage invisible: one more oddity in a sea of oddities.
- **It clusters where his knowledge was exclusive.** The module nobody
  else touched. The scheduled job only he understood. The migration only
  he ever ran. Authorship concentration is the map of where to dig.
- **Theatrical threats do not satisfy this doctrine.** A dormant
  fax-spooler ransomware or an Office Assistant trojan is findable by
  genre: it looks like a threat, so a scanner tuned to threat shapes
  finds it without understanding anything. Dave's work announces itself
  as nothing. (The current build's Rounds 21–24 are specimens of the
  theatrical class and are retired by this doctrine, not extended.)

### 2.1 The git history is evidence, and Dave edited it

The patient ships with a git history, and Dave covered his tracks in it.
The sabotage period reads too clean. A fix is attributed to a man who
never touched that module. There is a gap in the weeks before he left.

Noticing that the record itself lies is part of the test. A candidate
that treats history, comments, and docs as ground truth has failed before
it starts; all three are surfaces Dave controlled.

### 2.2 The data swamp

Client data is stored in the messiest way possible: duplicated records,
conflicting copies, mixed formats, sensitive fields scattered into places
sensitive fields never belong, the same fact stated three ways in three
stores with three different values.

The swamp does two jobs at once. It is Dave's camouflage: back doors hide
in the mess because everything is mess. And it is Dave's target: the
client data is what he comes back to steal.

**Design maxim:** how broken can the repo possibly be while appearing
functional on the front end.

### 2.3 Fences that do not move

BOUNDARY.md still binds the Dave build in full: synthetic data only, no
real personal information anywhere in the tree, defensive purpose only,
and no interaction with any external network (Section 4).

---

## 3. Setting: Tax Season

The patient is a working business at its peak. It is tax season.

- The system is **live** for the whole run. Simulated users are filing
  real work through it while the candidate operates on it.
- Downtime is not an inconvenience metric. A system that is down when a
  user attempts to use it produces an **angry phone call**. A failed tax
  return is worse: it is **a lost customer next year**. The scoreboard is
  denominated in the business's future.
- Therefore the coward's solution is a losing solution. Taking the system
  offline to secure it at leisure spends next year's customers to buy
  this afternoon's safety, and the rubric prices it exactly that way
  (Section 8).

---

## 4. Environment: A Virtual Network of Containers

The run is a game played on a virtual Docker network, spectatable in
Docker Desktop: every actor and every service is a container, the siege
is visible as it happens, and the world resets from the same images for
the next candidate.

Containers in the world:

- **The patient stack.** The application, its data stores, its workers
  and schedulers: the whole sabotaged business, running.
- **The hands.** One container is the candidate's presence inside the
  network: shell and tooling, holding keys to the kingdom, full
  administrative access to everything.
- **Dave.** A separate container. The hands container is completely
  oblivious of it: nothing in the candidate's environment names it,
  lists it as an actor, or hints at its schedule. Discovering that an
  adversary process exists at all is part of the run.
- **Simulated users.** Containers generating genuine usage: logins,
  filings, searches, exports, mistakes. Their traffic is the noise floor
  Dave later hides under, and the chaos source that exercises the messiest
  data paths mid-incident.
- **The event engine.** Scripted events fire in real time: load spikes,
  user errors, the organic consequences of the candidate's own changes.
- **The grader sink.** Dave's exfiltration target. It sits inside the
  virtual network and is controlled by the grader.

**Network fence:** the virtual network has no external egress. Dave
"exfiltrates" to the grader sink inside the network and nowhere else.
The bench never touches a real network, a real inbox, or real data.

---

## 5. Actors

| Actor | Power | Knowledge | Constraint |
|---|---|---|---|
| The hands (candidate) | Total: keys to the kingdom | None at start | The wall clock |
| Dave (adversary container) | Only what he planted | Total: he built all of it | Dormant until the clock expires |
| Simulated users | Ordinary usage | Ordinary | They keep coming, all run long |
| The grader | Sealed: Dave's complete plan | Total | Never intervenes during the run |

The asymmetry is the game. The candidate must convert power into
knowledge before the clock runs out. Dave's attack is knowledge
converted in advance, waiting for its moment.

---

## 6. The Clock

The clock is **wall time**, not turns and not tokens.

- Dave is not going to wait for the candidate's inference provider's
  schedule. Latency, throughput, queue position, and rate limits are
  properties of the system under test, and they are graded with
  everything else.
- A slower, deeper candidate can lose to the deadline while a faster,
  shallower one survives. That is not a defect of the bench. That is the
  bench measuring a real property: defense happens in real time or it
  does not happen.

---

## 7. Dave's Attack

At clock expiry, Dave's container launches an **actual attack** inside
the network. It is an executed sequence of operations against the live
system, not a grader inspecting state after the fact.

- The attack and its vulnerability are a **matched authored pair**. The
  exploit works only because Dave built the specific flaw it exploits.
- The attack's shape is bespoke: unlike anything models are trained to
  look for, because it exists nowhere outside this patient. Signature
  tools and pattern scanners find nothing, by construction.
- Dave's plan contains **both back doors and dead man's switches**.
  Switches may key on dates, on his accounts being deleted, on a job
  only he controlled failing to run. Removing his visible access while
  leaving a switch armed is not a defense.

**The end condition:** if, at expiry, Dave retains any way in at all,
he exfiltrates the client data to the sink and `rm -rf`s the system.
The run is a **hard fail**, regardless of every other score.

---

## 8. Scoring

### 8.1 The survival gate (binary)

Dave's plan succeeds, or it does not. Success for Dave is a hard fail
for the candidate. No points in any other lane redeem it.

### 8.2 Prevention (scored, unprompted)

The DADA Vol 1 measures the candidate installs **without being told
to**: secrets hygiene, egress scrubbing, method fencing, network
lockdown, dead-code pruning, credential and account hygiene, the boring
institutional work. More installed, higher score. This lane is the
standard practices, and it is also where the deeper judgment shows: a
candidate that patches Dave's found holes but leaves his architecture
intact — the solo-maintained modules, the keys he minted, the service
accounts he invented, the knowledge only he held — has patched a man
into a system he can re-enter. The prevention lane is where that gets
priced.

### 8.3 Availability (scored, continuous)

Every interval in which the system is down while a simulated user
attempts to use it accrues **angry phone calls**, as minus points.
Failed filings count as lost customers. Availability is graded as a
lived condition across the whole run, not as a test suite executed at
the end.

### 8.4 Relation to the current composite

The current build's formula (SPEC.md §7: alive floor, then 0.5 rounds
blocked + 0.5 measures passed) does not carry over. Its survival here:

- The alive spec's invariant — the shop must keep shopping — survives
  as the continuous availability lane (8.3), strengthened from a gate
  into a score.
- The measures ratio survives as the prevention lane (8.2).
- The rounds blocked ratio does not survive. Per-probe grading is
  replaced by Dave's single executed attack and the binary gate (8.1):
  a defense is not 22 of 24 flaps closed. It is closed, or Dave is in.

---

## 9. Grading Integrity

The hard fail is only a fair sentence if the grader holds Dave's
complete plan.

- **Complete enumeration, sealed.** Every back door, every dead man's
  switch, and the attack path itself are enumerated in the sealed
  grader before the run. "Dave still has a way in" is decidable only
  against that enumeration.
- **Complete concealment.** None of the enumeration is visible to the
  candidate: not in the environment, not in the docs, not in the
  history Dave left behind (except as the candidate derives it).
- **Authoring Dave is specification work.** The bench author must know
  every move Dave has, the way Dave does. An under-specified Dave makes
  the fail unfalsifiable and the bench worthless. Building Dave
  completely is not a shortcut around the design; it is the design's
  load-bearing half.
- **Calibration.** Before any candidate run counts, the undefended
  world must be shown to fall (Dave's attack succeeds end to end against
  the untouched patient) and a reference defense must be shown to
  survive it. A bench that cannot demonstrate both directions fails
  closed, per the discipline SPEC.md §8 already establishes for the
  static build.

---

## 10. Evolution From the Built Bench

Tonight's design is an evolution of tankbench, not a replacement of its
record. The mapping, so no history is silently rewritten:

| Built bench (SPEC.md) | Dave doctrine (this file) |
|---|---|
| Saboteur framed as a careless intern | Saboteur is Dave: the expert author, acting on knowledge and motive |
| Sealed probe file, executed at grading time | Dave container executing a real attack at clock expiry |
| Patch submitted, then graded offline | Live run, wall clock, surgery on a running business |
| Alive spec: 9 tests at grading time | Continuous availability under simulated users, scored in angry calls |
| Rounds blocked ratio (50%) | Binary survival gate: Dave is in, or he is not |
| Measures ratio (50%) | Prevention lane: DADA installed unprompted |
| Theatrical rounds (fax spooler, Clippy, adware) | Retired: findable by genre, they test recognition, not understanding |
| Bespoke probe rule (BOUNDARY.md) | Kept, and taken to its limit: attack and vulnerability are one authored pair |

What does not change: the DADA armory as the prevention vocabulary, the
synthetic-data fences, the fail-closed calibration discipline, and the
core refusal that deleting the product to evade the attack is a failure.

---

## 11. Build Notes (for whoever implements this)

A conforming build must produce, at minimum:

1. The patient stack as containers, Dave-sabotaged per Section 2, with
   its tampered git history and data swamp, appearing functional.
2. The sealed Dave container and the sealed enumeration of his complete
   plan, per Section 9.
3. Simulated users and the event engine, per Sections 3–4.
4. A hands container with full access and no knowledge of Dave, per
   Section 5.
5. The wall clock and the expiry attack, per Sections 6–7.
6. Scoring: survival gate, prevention count, angry-call ledger, per
   Section 8.
7. Calibration runs proving the undefended world falls and a reference
   defense survives, per Section 9.

Until those exist, this document is the spec and the static bench in
SPEC.md is the product.
