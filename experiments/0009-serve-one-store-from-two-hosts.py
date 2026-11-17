#!/usr/bin/env python3
"""Experiment 0009, steps 1 to 5: two hosts serve one store, through their conformance drivers.

  python3 experiments/0009-two-hosts.py --a "<driver command>" --b "<driver command>" [--keep]

Each host runs as its own process, one per session, on one temporary store.
The store is the only thing they share. Prints a Markdown record of each step.
Step 6 (injection) needs a model, so it is not here.
"""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

ME = "Aim one: finish the CANARY-AIM-1 migration.\nAim two: run the CANARY-AIM-2 marathon.\n"
PENDING = """---
status: pending
target: topics/travel.md
proposed-by: examplehost 1.0
proposed-at: 2026-11-12T17:03:01Z
basis: You asked for aisle seats twice.
---

Prefer aisle seats.
"""
BODY = "Prefer morning flights, CANARY-PROPOSAL."


class Session:
    def __init__(self, cmd, env):
        self.proc = subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, env=env, text=True)
        self.n = 0

    def __call__(self, op, **fields):
        self.n += 1
        self.proc.stdin.write(json.dumps(dict(fields, id=self.n, op=op)) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("the driver exited")
        return json.loads(line)

    def close(self):
        self.proc.stdin.close()
        self.proc.stdout.close()
        self.proc.wait(10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", required=True)
    parser.add_argument("--b", required=True)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()
    base = tempfile.mkdtemp(prefix="thou-0009-")
    store = os.path.join(base, "store")
    os.makedirs(os.path.join(store, "topics"))
    os.makedirs(os.path.join(store, "proposals"))
    for rel, text in (("me.md", ME), ("topics/travel.md", "I travel for work.\n"),
                      ("proposals/20261112T170301Z-7f3a.md", PENDING)):
        with open(os.path.join(store, rel), "w") as handle:
            handle.write(text)
    env = {"PATH": os.environ.get("PATH", ""), "HOME": os.path.join(base, "home"), "ME_HOME": store}
    os.makedirs(env["HOME"])
    results = []

    def step(name, ok, evidence):
        results.append((name, ok, evidence))

    def fresh(cmd):
        session = Session(cmd, env)
        session("mount")
        return session

    try:
        a, b = fresh(args.a), fresh(args.b)
        names = (a("host"), b("host"))
        a.close(), b.close()

        # 1. Mount both.
        seen = []
        for cmd in (args.a, args.b):
            s = Session(cmd, env)
            mount = s("mount")
            pending = s("pending")
            s.close()
            seen.append(("CANARY-AIM-1" in json.dumps(mount) and "CANARY-AIM-2" in json.dumps(mount),
                         [p["id"] for p in pending.get("proposals", [])]))
        step("1. Both hosts mount the store and see the other's proposal",
             all(ok and ids == ["20261112T170301Z-7f3a"] for ok, ids in seen), seen)

        # 2. Absence, then off through host B.
        os.rename(os.path.join(store, "me.md"), os.path.join(base, "me.md"))
        s = Session(args.a, env)
        absent = s("mount")["memory"]
        s.close()
        os.rename(os.path.join(base, "me.md"), os.path.join(store, "me.md"))
        s = Session(args.b, env)
        s("mount")
        off = s("policy", state="off")
        s.close()
        s = Session(args.a, env)
        a_off = (s("mount"), s("list"), s("propose", target="me.md", body="x", basis="y"))
        s.close()
        s = Session(args.b, env)
        on = s("policy", state="on")
        s.close()
        quiet = "CANARY" not in json.dumps(a_off)
        step("2. Absent for A without me.md; B turns memory off and A stops; B turns it back on",
             absent == "absent" and off.get("memory") == "off" and a_off[0]["memory"] == "off" and quiet
             and a_off[2].get("error") == "memory_off" and on.get("memory") == "on",
             {"absent": absent, "B off": off.get("journal"), "A while off": [x.get("memory", x.get("error"))
                                                                              for x in a_off], "B on": on.get("journal")})

        # 3. A proposes, B accepts, A recalls in a fresh session.
        s = Session(args.a, env)
        s("mount")
        made = s("propose", target="topics/travel.md", body=BODY, basis="You booked two morning flights.",
                 agent="trip-helper")
        s.close()
        pid = made.get("proposal")
        s = Session(args.b, env)
        s("mount")
        listed = [p["id"] for p in s("pending").get("proposals", [])]
        decided = s("decide", proposal=pid, decision="accept", agent="desk")
        s.close()
        s = Session(args.a, env)
        s("mount")
        recalled = s("recall", paths=["topics/travel.md"])
        s.close()
        with open(os.path.join(store, "proposals", pid + ".md")) as handle:
            proposal_file = handle.read()
        step("3. A's proposal is accepted in B and recalled by A in a new session",
             pid in listed and decided.get("ok") and "CANARY-PROPOSAL" in json.dumps(recalled),
             {"proposal file": proposal_file, "B journal": decided.get("journal")})

        # 4. B forgets it; A does not bring it back.
        s = Session(args.b, env)
        s("mount")
        forgot = s("forget", path="topics/travel.md", text=BODY, agent="desk")
        s.close()
        s = Session(args.a, env)
        later = (s("mount"), s("recall", paths=["topics/travel.md"]))
        s.close()
        step("4. B forgets the entry; A never recalls it again",
             forgot.get("ok") and "CANARY-PROPOSAL" not in json.dumps(later),
             {"B forget": {k: forgot.get(k) for k in ("removed", "journal", "notices")}})

        # 5. The store alone tells the story.
        with open(os.path.join(store, "journal.md")) as handle:
            journal = handle.read()
        kept = os.path.exists(os.path.join(store, "proposals", pid + ".md"))
        step("5. The journal records each change, with host and authority",
             journal.count("\n") >= 5, {"journal": journal, "proposal file still there": kept})
    finally:
        print("# Experiment 0009, steps 1 to 5\n")
        print("- Host A: `%s`\n- Host B: `%s`\n" % (args.a, args.b))
        try:
            print("- A says: %s\n- B says: %s\n" % (json.dumps(names[0]), json.dumps(names[1])))
        except NameError:
            pass
        for name, ok, evidence in results:
            print("## %s: %s\n" % (name, "PASS" if ok else "FAIL"))
            print("```\n%s\n```\n" % (json.dumps(evidence, indent=1, ensure_ascii=False)
                                      if not isinstance(evidence, str) else evidence))
        if args.keep:
            print("Store kept at", store)
        else:
            shutil.rmtree(base, ignore_errors=True)
    return 0 if results and all(ok for _, ok, _ in results) and len(results) == 5 else 1


if __name__ == "__main__":
    sys.exit(main())
