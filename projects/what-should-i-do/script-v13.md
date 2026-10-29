# WHAT SHOULD I DO?

Script v13.2 (Oct 29). v13.1 plus Rudy's notes on the first cut: "traceability" for "provenance", and the last line says "Check out our website." One narrator (male, voice-over). Alex never speaks. No pronouns for Alex.

What Rudy's notes on v12 changed:
- No fintech. The study never covered a fintech company, so Alex is just "a software developer".
- The viewer knows about the refunds and Alex doesn't, and the narration says so: "We can see it. Alex can't."
- After the overload, the camera pans out: Alex is not alone. Other developers, same flood.
- "What should I do?" grows from Alex's question into everyone's question, amid the speculation.
- The study grows on screen: 860, then a year later, wider, across companies and domains.
- Take two has to be visibly better: the same task goes well because Alex has the guidelines.
- The build-notices example and "work involving people" are gone. After Alex's story, the close is its own short
  chapter: the guidelines as a shared vocabulary, and as agent skills.

Running length: about 415 spoken words, about 2:45.

---

## 1. COLD OPEN

**MONTAGE.** Fast cuts, one per beat: an agent writing a whole feature; *AI review: 14 comments*; *Draft reply to
customer ready*. Faster and faster, then freeze.

> **NARRATOR (V.O.)**
> Developers have more help than ever. And less certainty about how to use it.

## 2. ALEX

**INT. OFFICE. DAY.** The frozen screen pulls back: Alex's monitor. ALEX (yellow sweater, curly hair, tea).

> **NARRATOR (V.O.)**
> Meet Alex, a software developer.

Alex types into the agent: *Move billing to the new payments system.* The agent races. A counter rolls and stops:
**63 files changed.**

> **NARRATOR (V.O.)**
> Alex asks an AI agent to move billing to a new payments system. Minutes later, sixty-three files have changed.

The camera dives through the stack of files and stops on **File 41**. One line glows:
`if (refund.amount > 10000) autoApprove(refund)`.

> **NARRATOR (V.O.)**
> Buried in file forty-one, the agent made a call nobody asked for. Large refunds now approve themselves.

The camera pulls back out past Alex's shoulder. Alex is looking at file 1. The glow stays on screen for us, far
down the stack, where Alex isn't looking.

> **NARRATOR (V.O.)**
> We can see it. Alex can't.

Alex reads. Pull request cards slide into the sidebar, each with a teammate's face: *Review requested: Alex.* The
stack grows. The release board behind Alex flips: **RELEASE TODAY. OWNER: ALEX.**

> **NARRATOR (V.O.)**
> Alex starts reading. Then the team's changes arrive for review. It's more code than Alex can absorb. And whatever ships, Alex is accountable for it.

## 3. NOT ALONE

The camera pulls up and out. Alex's desk is one of a row, then a floor, then a grid of desks seen from above. At every
desk, the same picture: an agent racing, a counter rolling, a stack of reviews growing.

> **NARRATOR (V.O.)**
> Alex is not alone.

Around the grid, headlines and hot takes swirl past, each saying something different.

> **NARRATOR (V.O.)**
> Amid all the speculation, they're all left with one question.

Every screen in the grid goes dark at once. One line of type across all of them: **WHAT SHOULD I DO?** (title)

> **NARRATOR (V.O.)**
> What should I do?

The title breaks into the paper's question, written across the grid:

> **NARRATOR (V.O.)**
> With each new AI release, it comes back in a new form. How much of my daily work should I hand to AI, and what must I still own?

## 4. WE ASKED

The grid of desks becomes a night sky of lights. A super: **Our study.** A counter: **860 developers at Microsoft.**

> **NARRATOR (V.O.)**
> So we went to developers in the trenches. Eight hundred and sixty of them, at a frontier tech company, Microsoft.

From each light rise two kinds of lanterns, warm (*sought*) and cool (*resisted*), drifting across five lanes laid out
like the lifecycle: **Design & Planning · Development · Quality & Risk · Infrastructure & Ops · Meta-work.**

> **NARRATOR (V.O.)**
> We asked how they wanted to integrate AI responsibly in their work, and where they resisted it, across the software lifecycle.

The lanterns settle as cards in the five lanes, each lane lighting as the narrator names it. Six more cards float
above all of them.

> **NARRATOR (V.O.)**
> From their answers, we synthesized thirty-five developer-facing guidelines. Across five kinds of software work: development, design and planning, quality and risk, infrastructure and operations, and meta-work. And six cross-cutting ones.

A calendar flips: **One year later.** The AI tools around the cards change shape; the cards hold. The sky widens and
new lights join the crowd. The counter climbs: **860 → 1,118.** Over the whole crowd, one per beat: **Microsoft.
GitHub. Pfizer.**

> **NARRATOR (V.O.)**
> A year later, as AI and developers' experiences kept evolving, we went wider. Across companies and domains. Microsoft. GitHub. Pfizer.

Three bars fill: **Clear 92% · Relevant 91% · Want to adopt 89%.**

> **NARRATOR (V.O.)**
> Developers found the guidelines clear and relevant. And eighty-nine percent wanted to adopt them.

The cards lift into lines of type, one per beat: **Refine your craft. · Delegate what you can verify. · Demand transparency
and traceability. · Keep judgment and accountability.**

> **NARRATOR (V.O.)**
> They described using AI to refine their craft and delegate work they could effectively verify, while demanding transparency and traceability, and keeping judgment and accountability for themselves.

## 5. TAKE TWO

The words fall into Alex's monitor. A clapperboard snaps: **TAKE TWO.** Same desk, same task, tea warm.

> **NARRATOR (V.O.)**
> Back to Alex. Take two. This time, with the guidelines.

Alex types the task, then adds: *Plan first.* The agent shows a four-step plan. Alex reads it, changes a step,
approves. Guideline chip (DV1).

> **NARRATOR (V.O.)**
> Alex hands off the routine work, but demands a plan of action first.

Alex adds: *If anything is unclear, ask.* The agent stops on a question card: *The spec doesn't say how to handle
refunds over $10,000. Approve them automatically, or hold them for review?* Alex taps **Hold for review.** Guideline
chip (CC1); the word *inferred* glows for a beat.

> **NARRATOR (V.O.)**
> Alex demands that the agent ask for clarification instead of acting on inferred context. So the agent asks about large refunds. Alex gets to decide.

Alex adds: *Small pull requests. State your assumptions.* The work comes back as four small pull requests, each with
**Assumptions** at the top. The first one says: *Refunds over $10,000: held for review (Alex).* Alex reads each one
to the end. Guideline chips (CC5, CC4).

> **NARRATOR (V.O.)**
> Alex also demands its work in self-contained pieces Alex can review, with its assumptions and sources in plain view. Four small pull requests. Alex can read every one.

The release board flips: **RELEASE TODAY ✓. OWNER: ALEX.** Alex lifts the tea.

> **NARRATOR (V.O.)**
> This time, Alex better understands what ships.

## 6. FOR YOU AND YOUR AGENTS

The camera pulls out of Alex's office, back up to the grid of desks, now in daylight.

> **NARRATOR (V.O.)**
> We offer these guidelines from developers in the trenches, to other developers in the trenches.

One table: a team around guideline cards, talking them through, moving one card.

> **NARRATOR (V.O.)**
> As a shared vocabulary for teams, and as skills for their agents: instructions an agent loads when a task calls for them.

Into a screen: the guideline cards fold into `SKILL.md`; an agent loads it. The real site's skill generator: toggles
on, *Your skill is ready.*

> **NARRATOR (V.O.)**
> Whether agents that follow them improve developers' work is still open. Try them, and tell us how it goes.

End card: **What Should I Do?** Under it, large: **aka.ms/ai-where-it-matters**. Authors below.

> **NARRATOR (V.O.)**
> Check out our website.

**END.**

---

## Before and after (same task)

| Take one, without the guidelines | Take two, with the guidelines |
|---|---|
| The agent infers how to handle large refunds, silently | The agent asks; Alex decides (CC1) |
| 63 files at once | A plan first (DV1), then four small pull requests (CC5) |
| Nothing says what was assumed | Assumptions at the top of each pull request (CC4) |
| More code than Alex can absorb | Alex reads every one |
| Alex is accountable for what ships | Alex better understands what ships |

## Guideline wording (Table II)

- **DV1:** Use AI to automate routine, verifiable development tasks under human oversight; demand AI to produce
  reviewable steps and plan of action.
- **CC1:** Demand AI to ask for clarification instead of acting on missing or inferred context.
- **CC4:** Demand AI to back its claims with cited, verifiable evidence, and to clearly state its assumptions,
  reasoning, scope, and uncertainty.
- **CC5:** Demand AI to deliver its output in atomic, self-contained pieces a human can review.

## Sources

| Line | Source in the paper |
|---|---|
| More help, and less certainty about how to use it | Sec. I, paragraph 1 |
| More contributions than they can absorb | Sec. I, paragraph 4 |
| Developers remain accountable for the result | Sec. I, paragraph 2; Abstract |
| Speculations abound about the right ways | Abstract, sentence 1 |
| The same question back in a new form; how much of my daily work should I hand to AI, and what must I still own? | Sec. I, paragraph 2 (exact quote) |
| Developers in the trenches; a frontier technology company | Sec. I; Abstract |
| 860 developers at Microsoft; where they sought and resisted AI, across SE tasks | Abstract; Sec. I; Table I |
| 35 developer-facing guidelines: 29 across five categories of SE work, 6 cross-cutting | Abstract |
| A year later, as AI changed; across companies and domains; Microsoft, GitHub, Pfizer; 1,118 in total | Abstract; Sec. I |
| Clear (92%), relevant (91%), wanted to adopt (89%) | Abstract |
| Refine their craft, delegate verifiable work, keep judgment and accountability | Abstract |
| Effectively verify | Sec. I (contributions paragraph) |
| Demanding transparency and traceability (CC4 evidence and assumptions; traceable assumptions, sources and findings) | Table II; Sec. IV |
| Advice from in-the-trenches developers to other in-the-trenches developers; a shared vocabulary for teams | Abstract, last sentence |
| Skills: instructions an agent loads when a task calls for them | Sec. V-B |
| Whether agents that follow these guidelines improve developers' work is open | Sec. V-B, future work |
| aka.ms/ai-where-it-matters | The guidelines site |

Invented for the film and never attributed to the paper: Alex, the billing task, the file counts, the refund rule,
the team's pull requests, and the on-screen notifications.
