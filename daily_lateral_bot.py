#!/usr/bin/env python3
"""
Daily Lateral Thinking Bot
--------------------------
Posts one lateral-thinking exercise to Slack each day.

Every exercise maps to a technique with real evidence behind it for
developing divergent / lateral thinking:
  - Random Entry (random-word association)   de Bono
  - SCAMPER (structured modification)         Eberle / Osborn
  - Provocation "PO" (deliberate wrong step)  de Bono
  - Reversal (flip the goal)                  de Bono
  - Bad Ideas (reverse brainstorming)
  - Constraint-based ideation
  - Remote-Associates / insight puzzle        Mednick; Kounios & Beeman
  - Six Thinking Hats mini-pass               de Bono

The exercise bank is shuffled once with a fixed seed so the order is
varied but stable, then cycled by date -> you never get a repeat until
you've worked through the whole bank.

Requires:  SLACK_WEBHOOK_URL  (environment variable)
Optional:  BANK_SEED          (int, to reshuffle your rotation)
"""

import os
import sys
import json
import random
import datetime
import urllib.request

# ---------------------------------------------------------------------------
# Exercise bank. Each item: (technique, prompt, how-to-work-it)
# ---------------------------------------------------------------------------
EXERCISES = [
    ("Random Entry",
     "Take today's date number (e.g. the 14th) and open any book to that page. "
     "Grab the first concrete noun you see. Now force a link between that noun and "
     "a problem you're currently stuck on.",
     "The point isn't relevance, it's the bridge you build to get there — that bridge is the new idea."),

    ("Random Entry",
     "Random word: LIGHTHOUSE. Connect it to something you're trying to improve at work "
     "or in a personal project.",
     "List every attribute of the word (isolated, guides, warns, rotates, stands alone) and map each onto your problem."),

    ("Random Entry",
     "Random word: MUSHROOM. Use it to generate three ideas for a habit, routine, or product you use daily.",
     "Force at least one idea from a property you'd normally ignore — how it grows in the dark, how it spreads underground."),

    ("Random Entry",
     "Pick the next physical object you can see to your left. Apply it as a metaphor to a decision you're avoiding.",
     "Ask: if this decision worked like that object, what would I do next?"),

    ("SCAMPER",
     "Take a routine you do every day (your commute, your morning, how you run meetings). "
     "Run it through SCAMPER: Substitute one part, Combine two steps, Adapt it from another field.",
     "You only need one of the seven to click. Write the three variants, keep the best."),

    ("SCAMPER",
     "Pick a product you own and hate slightly. Apply 'Eliminate' and 'Reverse': "
     "what happens if you remove its main feature, or run it backwards?",
     "Removing the 'obvious' core often reveals what the thing is really for."),

    ("SCAMPER",
     "Choose a piece of your work. Apply 'Put to another use': who outside your field would pay for this, and why?",
     "Same object, new context. This is where side-projects and pivots are born."),

    ("SCAMPER",
     "Take an idea you already have and 'Magnify' then 'Minify' it: what does the 10x version look like? The pocket-sized version?",
     "The extremes usually expose an assumption you didn't know you were making."),

    ("Provocation (PO)",
     "PO: your phone has no screen. Design how you'd still get through your day.",
     "A provocation is deliberately impossible. Don't judge it — extract a principle and bring that principle back to reality."),

    ("Provocation (PO)",
     "PO: the customer pays only if they DON'T use the product. What business model does that force?",
     "de Bono's move: take the outlandish statement and ask what useful idea 'moves' out of it."),

    ("Provocation (PO)",
     "PO: meetings are held while everyone is walking and can't take notes. What survives?",
     "Whatever survives is the essential part. Keep that; question the rest."),

    ("Provocation (PO)",
     "PO: the factory is downstream of itself (de Bono's classic). Apply the same logic to your own work — "
     "what would it mean to consume your own output first?",
     "This exact provocation became real pollution law. Provocations can ship."),

    ("Reversal",
     "Whatever your current goal is, invert it: how would you guarantee the OPPOSITE outcome?",
     "List the ways to fail on purpose. Each one is a hidden lever you can now pull the other direction."),

    ("Reversal",
     "You want people to engage more with something. Instead ask: how would I make them ignore it completely?",
     "The avoidance list is usually more honest and specific than the 'how to improve' list."),

    ("Reversal",
     "Pick a process you want to speed up. Ask instead: how could I make it as slow as possible?",
     "Reverse the slow-down levers and you've found your acceleration points."),

    ("Bad Ideas",
     "Spend 5 minutes generating the WORST possible solutions to a current problem. Aim for at least 8 terrible ones.",
     "Then flip each: what's the good version hiding inside the bad one? Bad-idea brainstorming lowers the fear that kills divergence."),

    ("Bad Ideas",
     "What's the most unethical, lazy, or absurd way to solve today's biggest task? Write three.",
     "Removing the 'must be sensible' filter is what unlocks the associative network. Extract the usable kernel afterward."),

    ("Constraint",
     "Solve a current problem using only things that cost nothing and can be done in 10 minutes.",
     "Tight constraints force associative leaps — they're a feature, not a limitation."),

    ("Constraint",
     "Explain your current project's core idea in exactly 6 words. Then in 3.",
     "Radical compression surfaces the true concept and strips the borrowed assumptions."),

    ("Constraint",
     "Design a solution to a nagging annoyance assuming you can't use any screen or app.",
     "Removing the default tool forces the perception-shift that lateral thinking is about."),

    ("Remote Associates",
     "Find ONE word that connects: COTTAGE / SWISS / CAKE.",
     "Insight puzzle (answer: CHEESE). Let it sit; notice the 'aha' arrive rather than grinding logically."),

    ("Remote Associates",
     "Find ONE word that connects: CREAM / SKATE / WATER.",
     "Answer: ICE. These train the right-hemisphere leap that fMRI links to the 'Aha!' moment."),

    ("Remote Associates",
     "Find ONE word that connects: SHOW / LIFE / ROW.",
     "Answer: BOAT. If you're stuck, look away, relax — insight favours a defocused mind."),

    ("Remote Associates",
     "Find ONE word that connects: NIGHT / WRIST / STOP.",
     "Answer: WATCH. Notice: the solution tends to appear whole, not step-by-step."),

    ("Remote Associates",
     "Find ONE word that connects: DUCK / FOLD / DOLLAR.",
     "Answer: BILL. Incubation helps — glance at it now, let the answer surface later."),

    ("Six Hats",
     "Take a decision you're mulling. Do three fast 60-second passes: pure facts (White), pure feelings (Red), pure risks (Black).",
     "Separating the modes stops one from drowning the others — that's the whole point of the hats."),

    ("Six Hats",
     "For an idea you like, deliberately wear the Black hat for 2 minutes: only downsides. Then Yellow: only upsides.",
     "Forcing a single lens per pass produces sharper material than mixed 'balanced' thinking."),

    ("Random Entry",
     "Random word: ORIGAMI. Apply to how you organise your time or space.",
     "Attributes: folding, one sheet, reversible, instructions. Which maps onto your week?"),

    ("Provocation (PO)",
     "PO: you must give away your best idea for free, today. What would you build knowing that?",
     "Scarcity-removal provocations expose what you're really protecting and why."),

    ("Reversal",
     "Instead of 'how do I get more done', ask 'how do I do dramatically less and still win?'",
     "The subtraction path is a distinct branch most people never walk down."),

    ("SCAMPER",
     "Pick a habit. 'Combine' it with something you already do effortlessly (habit-stacking).",
     "Combination is the most underused SCAMPER verb and the highest-yield for personal systems."),

    ("Constraint",
     "Come up with 10 uses for a paperclip in 3 minutes. Go for quantity, no judging.",
     "Guilford's classic divergent-thinking warmup — fluency and flexibility improve with reps."),

    ("Random Entry",
     "Random word: VOLCANO. Connect it to a relationship or conversation you want to handle better.",
     "Pressure, dormancy, warning signs, eruption — pick the attribute that stings and sit with it."),

    ("Bad Ideas",
     "List 5 ways to make your morning routine actively worse. Then reverse-engineer improvements.",
     "The failure list is a specific, actionable inverse of a to-do list."),

    ("Provocation (PO)",
     "PO: this task has already been finished by someone else. Where would you look for their version?",
     "Assuming the solution exists reframes 'create' into 'find and adapt' — often faster and more lateral."),
]

# ---------------------------------------------------------------------------
# Selection: stable shuffle, then cycle by day so nothing repeats until the
# whole bank has been used.
# ---------------------------------------------------------------------------
def pick_exercise(today: datetime.date):
    seed = int(os.environ.get("BANK_SEED", "42"))
    order = list(range(len(EXERCISES)))
    random.Random(seed).shuffle(order)
    days = (today - datetime.date(2025, 1, 1)).days
    return EXERCISES[order[days % len(order)]]


def build_payload(technique, prompt, howto, today):
    return {
        "text": f"Lateral thinking exercise ({technique})",  # notification fallback
        "blocks": [
            {"type": "header",
             "text": {"type": "plain_text", "text": "🧠 Daily Lateral Thinking"}},
            {"type": "context",
             "elements": [{"type": "mrkdwn",
                           "text": f"*{today:%A %d %B}*  ·  technique: *{technique}*"}]},
            {"type": "section",
             "text": {"type": "mrkdwn", "text": f"*Today's exercise*\n{prompt}"}},
            {"type": "section",
             "text": {"type": "mrkdwn", "text": f"_How to work it:_ {howto}"}},
            {"type": "context",
             "elements": [{"type": "mrkdwn",
                           "text": "Spend even 60 seconds on it — de Bono: little and often beats one big session."}]},
        ],
    }


def post_to_slack(payload):
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        print("ERROR: SLACK_WEBHOOK_URL not set.", file=sys.stderr)
        sys.exit(1)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        if resp.status != 200:
            print(f"ERROR: Slack returned {resp.status}", file=sys.stderr)
            sys.exit(1)
    print("Posted today's exercise to Slack.")


if __name__ == "__main__":
    today = datetime.date.today()
    technique, prompt, howto = pick_exercise(today)
    if "--dry-run" in sys.argv:
        print(f"[{technique}] {prompt}\n  -> {howto}")
    else:
        post_to_slack(build_payload(technique, prompt, howto, today))
