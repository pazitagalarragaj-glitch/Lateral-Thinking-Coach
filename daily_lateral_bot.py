#!/usr/bin/env python3
"""
Daily Lateral Thinking Bot
--------------------------
Posts one lateral-thinking exercise to Slack each day.

Each day = a random SCENARIO run through a random TECHNIQUE lens, so every
prompt is concrete (never "think of a current problem"). Techniques all map
to methods with evidence behind them for developing divergent/lateral thinking:
  Random Entry, SCAMPER, Provocation "PO", Reversal, Bad Ideas,
  Constraint, Six Thinking Hats, plus self-contained Remote-Associates
  insight puzzles (Kounios & Beeman's "Aha!" research).

Scenarios and techniques are each shuffled once with a fixed seed, then cycled
by date, so combinations stay varied and don't repeat for a long stretch.

Requires:  SLACK_WEBHOOK_URL
Optional:  BANK_SEED  (int, reshuffles your rotation)
"""

import os
import sys
import json
import random
import datetime
import urllib.request

# ---------------------------------------------------------------------------
# Concrete scenarios. Mix of global problems, everyday predicaments, business,
# and absurd — all specific enough to start on immediately.
# ---------------------------------------------------------------------------
SCENARIOS = [
    "world hunger",
    "you overslept and are 20 minutes from missing an international flight",
    "a coffee shop that's always empty despite great coffee",
    "getting people to actually drink enough water",
    "a city where nobody can find parking",
    "your phone battery dies exactly when you need directions in a foreign city",
    "reducing plastic waste in the ocean",
    "a gym that's packed in January and empty by March",
    "you locked yourself out of your apartment at midnight in the rain",
    "getting kids to eat vegetables",
    "a bookshop competing against Amazon",
    "traffic jams during rush hour",
    "you have to give a wedding speech and forgot to prepare anything",
    "loneliness among elderly people living alone",
    "a restaurant where the food is great but reviews are terrible",
    "remembering people's names after you meet them",
    "your team's meetings always run 30 minutes over",
    "food that spoils before people can eat it",
    "you spilled coffee on your laptop an hour before a deadline",
    "convincing people to take the stairs instead of the elevator",
    "a museum that young people find boring",
    "your neighbour's dog barks all night",
    "getting a stubborn stain out of a favourite shirt with no supplies",
    "reducing burnout in hospital nurses",
    "a product nobody knows they need yet",
    "you're stuck in an elevator with a stranger for an hour",
    "making public transport feel safe at night",
    "a small town losing all its young people to big cities",
    "you have exactly €10 to feed yourself for three days",
    "getting strangers at a party to actually talk to each other",
    "reducing the amount of time people waste looking for their keys",
    "a language app people download but never open again",
    "you have to entertain a bored 6-year-old for two hours with nothing",
    "cutting the time patients wait in emergency rooms",
]

# Random words for the Random Entry technique
RANDOM_WORDS = [
    "LIGHTHOUSE", "MUSHROOM", "ORIGAMI", "VOLCANO", "MAGNET", "BEEHIVE",
    "MIRROR", "COMPASS", "SPONGE", "AVALANCHE", "CLOCKWORK", "RIVER",
    "SCAFFOLDING", "CONFETTI", "ANCHOR", "PRISM", "THERMOSTAT", "MOSAIC",
    "PENDULUM", "GREENHOUSE",
]

# Self-contained insight puzzles (no scenario needed)
PUZZLES = [
    ("COTTAGE / SWISS / CAKE", "CHEESE"),
    ("CREAM / SKATE / WATER", "ICE"),
    ("SHOW / LIFE / ROW", "BOAT"),
    ("NIGHT / WRIST / STOP", "WATCH"),
    ("DUCK / FOLD / DOLLAR", "BILL"),
    ("FLOWER / FRIEND / SCOUT", "GIRL"),
    ("PINE / CRAB / SAUCE", "APPLE"),
    ("BOARD / MAGIC / DEATH", "BLACK"),
    ("FOUNTAIN / BAKING / POP", "SODA"),
    ("BASKET / EIGHT / SNOW", "BALL"),
]

# ---------------------------------------------------------------------------
# Technique lenses. Each returns (technique_name, prompt, how_to_work_it).
# Scenario-based ones take a scenario (and sometimes a random word).
# ---------------------------------------------------------------------------
def t_bad_ideas(sc, word):
    return ("Bad Ideas",
            f"Generate at least 8 of the WORST possible solutions to: **{sc}**. "
            f"Make them genuinely terrible.",
            "Then flip each one — what good idea is hiding inside the bad one? "
            "Killing the 'be sensible' filter is what unlocks divergence.")

def t_reversal(sc, word):
    return ("Reversal",
            f"Take this: **{sc}**. Instead of solving it, ask: how would you make it "
            f"as BAD as possible on purpose? List 5 ways to guarantee the worst outcome.",
            "Now invert each — every failure lever is a hidden solution lever.")

def t_scamper(sc, word):
    return ("SCAMPER",
            f"Apply SCAMPER to: **{sc}**. Pick any three: Substitute, Combine, Adapt, "
            f"Modify, Put-to-other-use, Eliminate, Reverse.",
            "You only need one verb to click. Write three variants, keep the best.")

def t_provocation(sc, word):
    return ("Provocation (PO)",
            f"Provocation for: **{sc}**. State something deliberately impossible about it "
            f"(e.g. 'it solves itself overnight'), then work backwards.",
            "Don't judge the provocation — extract a usable principle and bring that back to reality.")

def t_random_entry(sc, word):
    return ("Random Entry",
            f"Random word: **{word}**. Force a connection between it and: **{sc}**.",
            "List the word's attributes, then map each onto the scenario. The bridge you build is the idea.")

def t_constraint(sc, word):
    return ("Constraint",
            f"Solve **{sc}** using only things that cost nothing and can be done in 10 minutes.",
            "Tight constraints force associative leaps — that's the feature, not the limit.")

def t_six_hats(sc, word):
    return ("Six Hats",
            f"Take **{sc}**. Do three fast 60-second passes: pure facts (White), "
            f"pure gut feeling (Red), pure risks (Black).",
            "Separating the modes stops one from drowning the others.")

SCENARIO_TECHNIQUES = [
    t_bad_ideas, t_reversal, t_scamper, t_provocation,
    t_random_entry, t_constraint, t_six_hats,
]

# ---------------------------------------------------------------------------
# Selection: cycle scenarios, techniques, and words independently by date.
# Every ~5th day is an insight puzzle instead, for variety.
# ---------------------------------------------------------------------------
def pick_exercise(today: datetime.date):
    seed = int(os.environ.get("BANK_SEED", "42"))
    rng = random.Random(seed)
    scen = SCENARIOS[:]; rng.shuffle(scen)
    tech = SCENARIO_TECHNIQUES[:]; rng.shuffle(tech)
    words = RANDOM_WORDS[:]; rng.shuffle(words)
    puz = PUZZLES[:]; rng.shuffle(puz)

    days = (today - datetime.date(2025, 1, 1)).days

    if days % 5 == 4:  # puzzle day
        triple, answer = puz[days % len(puz)]
        return ("Remote Associates",
                f"Find the ONE word that connects: **{triple}**",
                f"An insight puzzle — let it sit, look away, let the answer surface. (Answer: {answer})")

    builder = tech[days % len(tech)]
    sc = scen[days % len(scen)]
    word = words[days % len(words)]
    return builder(sc, word)


def build_payload(technique, prompt, howto, today):
    return {
        "text": f"Lateral thinking exercise ({technique})",
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
                           "text": "Even 60 seconds counts — little and often beats one big session."}]},
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
