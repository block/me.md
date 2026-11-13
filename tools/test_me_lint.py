"""Tests for me_lint: every conformance fixture, plus cases built at runtime
(symlinks, BOM, invalid UTF-8) so no symlink or odd bytes live in git."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.join(HERE, "me_lint.py")
FIXTURES = os.path.join(HERE, "..", "conformance", "fixtures")

ME = "# About me\n\nA fictional person.\n"


def run_lint(store, *extra):
    proc = subprocess.run([sys.executable, LINT, store] + list(extra),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return proc.returncode, proc.stdout, proc.stderr


def lint_json(store):
    code, out, _ = run_lint(store, "--json")
    return code, json.loads(out)


def flat(findings):
    return ["%s: %s" % (f["path"], f["message"]) for f in findings]


class FixtureTests(unittest.TestCase):
    def check_fixture(self, name):
        base = os.path.join(FIXTURES, name)
        with open(os.path.join(base, "expect.json")) as handle:
            expect = json.load(handle)
        store = os.path.join(base, "store")
        code, report = lint_json(store)
        self.assertEqual(code, expect["exit"])
        self.assertEqual(run_lint(store)[0], expect["exit"])
        if "present" in expect:
            self.assertEqual(report["present"], expect["present"])
        if "policy_state" in expect:
            state = report["policy"]["state"] if report["policy"] else None
            self.assertEqual(state, expect["policy_state"])
        for bucket in ("errors", "warnings", "notes"):
            lines = flat(report[bucket])
            for wanted in expect.get(bucket + "_contain", []):
                self.assertTrue(any(wanted in line for line in lines), (wanted, lines))
            singular = bucket[:-1] + "_count"
            if singular in expect:
                self.assertEqual(len(lines), expect[singular], lines)
        for key, value in expect.get("counts", {}).items():
            self.assertEqual(report["counts"][key], value, key)


def add_fixture_tests():
    for name in sorted(os.listdir(FIXTURES)):
        if os.path.isfile(os.path.join(FIXTURES, name, "expect.json")):
            setattr(FixtureTests, "test_fixture_" + name.replace("-", "_"),
                    lambda self, name=name: self.check_fixture(name))


add_fixture_tests()


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = os.path.join(self._tmp.name, "store")
        os.mkdir(self.root)
        self.put("me.md", ME)

    def put(self, rel, content, mode="w"):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode) as handle:
            handle.write(content)
        return path

    def errors(self):
        code, report = lint_json(self.root)
        return code, flat(report["errors"])

    def test_clean_store(self):
        self.assertEqual(self.errors(), (0, []))

    def test_symlink_inside_store(self):
        self.put("topics/real.md", "x\n")
        os.symlink("real.md", os.path.join(self.root, "topics", "link.md"))
        code, errors = self.errors()
        self.assertEqual(code, 1)
        self.assertTrue(any("topics/link.md" in e and "symlink" in e for e in errors), errors)

    def test_symlink_pointing_outside_is_not_followed(self):
        outside = os.path.join(self._tmp.name, "outside.md")
        with open(outside, "wb") as handle:
            handle.write(b"\xff\xfe not utf-8")
        os.symlink(outside, os.path.join(self.root, "watches.md"))
        code, errors = self.errors()
        self.assertEqual(code, 1)
        self.assertTrue(any("watches.md" in e and "symlink" in e for e in errors), errors)
        self.assertFalse(any("UTF-8" in e for e in errors), errors)

    def test_symlinked_folder_is_not_descended(self):
        elsewhere = os.path.join(self._tmp.name, "elsewhere")
        os.mkdir(elsewhere)
        with open(os.path.join(elsewhere, "bad.md"), "wb") as handle:
            handle.write(b"\xff")
        os.symlink(elsewhere, os.path.join(self.root, "topics"))
        code, errors = self.errors()
        self.assertEqual(code, 1)
        self.assertEqual(len(errors), 1, errors)

    def test_symlinked_root_is_allowed(self):
        link = os.path.join(self._tmp.name, "link-to-store")
        os.symlink(self.root, link)
        self.assertEqual(lint_json(link)[0], 0)

    def test_bom(self):
        self.put("topics/travel.md", b"\xef\xbb\xbf# Travel\n", mode="wb")
        code, errors = self.errors()
        self.assertEqual(code, 1)
        self.assertTrue(any("topics/travel.md" in e and "BOM" in e for e in errors), errors)

    def test_invalid_utf8(self):
        self.put("projects/trip.md", b"caf\xe9\n", mode="wb")
        code, errors = self.errors()
        self.assertEqual(code, 1)
        self.assertTrue(any("projects/trip.md" in e and "UTF-8" in e for e in errors), errors)

    def test_unknown_top_level_entries_are_not_read(self):
        self.put("notes.md", b"\xff", mode="wb")
        self.put(".git/config", b"\xff", mode="wb")
        self.assertEqual(self.errors(), (0, []))

    def test_status_comes_only_from_front_matter(self):
        text = ("---\nstatus: refused\ntarget: me.md\nproposed-by: examplehost 1.0\n"
                "proposed-at: 2026-11-12T17:03:01Z\nbasis: you said so\n---\n\nstatus: accepted\n")
        self.put("proposals/20261112T170301Z-7f3a.md", text)
        code, report = lint_json(self.root)
        self.assertEqual(code, 0)
        self.assertEqual(report["counts"]["proposals_refused"], 1)
        self.assertEqual(report["counts"]["proposals_accepted"], 0)

    def test_front_matter_grammar_is_strict(self):
        for index, fm in enumerate(("status: pending\n  nested: yes\n", "Status: pending\n",
                                    'status: "pen\\ding"\n', "status: pending\nstatus: pending\n")):
            text = "---\n%starget: me.md\nproposed-by: h\nproposed-at: 2026-11-12T17:03:01Z\nbasis: b\n---\nbody\n" % fm
            self.put("proposals/20261112T17030%dZ-7f3a.md" % index, text)
        code, errors = self.errors()
        self.assertEqual(code, 1)
        self.assertEqual(len(errors), 4, errors)

    def report(self):
        return lint_json(self.root)

    def proposal(self, status="pending", proposed_at="2026-11-12T17:03:01Z", body="Prefers aisle seats.\n",
                 extra=""):
        return ("---\nstatus: %s\ntarget: topics/travel.md\nproposed-by: examplehost 1.0\n"
                "proposed-at: %s\nbasis: you said so\n%s---\n\n%s" % (status, proposed_at, extra, body))

    def test_symlinked_policy_means_off(self):
        on = os.path.join(self._tmp.name, "on.json")
        with open(on, "w") as handle:
            handle.write('{"state": "on"}\n')
        os.symlink(on, os.path.join(self.root, "policy.json"))
        code, report = self.report()
        self.assertEqual(code, 0)
        self.assertEqual(report["policy"]["state"], "off")
        self.assertTrue(any("symbolic link" in w for w in flat(report["warnings"])))

    def test_symlinked_me_means_absent(self):
        os.remove(os.path.join(self.root, "me.md"))
        real = os.path.join(self._tmp.name, "real-me.md")
        with open(real, "w") as handle:
            handle.write(ME)
        os.symlink(real, os.path.join(self.root, "me.md"))
        code, report = self.report()
        self.assertEqual(code, 0)
        self.assertFalse(report["present"])
        self.assertTrue(any("store as absent" in w for w in flat(report["warnings"])))
        self.assertIn("store as absent", run_lint(self.root)[1])

    def test_non_ascii_digits_are_rejected(self):
        arabic = "٢٠٢٦"  # 2026 in Arabic-Indic digits
        self.put("proposals/20261112T170301Z-7f3a.md", self.proposal(proposed_at=arabic + "-11-12T17:03:01Z"))
        self.put("journal.md", "- %s-11-12T17:03:01Z | me.md | added an aim | host: h | authority: person direct\n"
                 % arabic)
        code, errors = self.errors()
        self.assertEqual(code, 1)
        self.assertTrue(any("proposed-at must be RFC 3339" in e for e in errors), errors)
        self.assertTrue(any("journal.md: line 1: time" in e for e in errors), errors)

    def test_key_with_no_value(self):
        text = self.proposal().replace("basis: you said so\n", "basis:\n")
        self.put("proposals/20261112T170301Z-7f3a.md", text)
        code, errors = self.errors()
        self.assertEqual(code, 1)
        self.assertTrue(any("basis has no value" in e for e in errors), errors)

    def test_white_space_body_is_empty(self):
        self.put("proposals/20261112T170301Z-7f3a.md", self.proposal(body=" \n\t\n"))
        code, errors = self.errors()
        self.assertEqual(code, 1)
        self.assertTrue(any("body is empty" in e for e in errors), errors)

    def test_watches_are_top_level_items_outside_fences(self):
        self.put("watches.md", "- one\n  - nested, part of one\n  wrapped line\n* two\n"
                               "```\n- not a watch\n~~~\n- still code\n```\n~~~\n* not a watch either\n~~~\n- three\n")
        code, report = self.report()
        self.assertEqual(code, 0)
        self.assertEqual(report["counts"]["watches"], 3)

    def test_decisions_need_journal_entries(self):
        self.put("proposals/20261112T170301Z-7f3a.md", self.proposal(status="accepted"))
        code, report = self.report()
        warnings = flat(report["warnings"])
        self.assertEqual(code, 0)
        self.assertTrue(any("no journal entry records this decision" in w for w in warnings), warnings)
        self.assertTrue(any("records the change this proposal made" in w for w in warnings), warnings)
        self.put("journal.md",
                 "- 2026-11-12T17:05:00Z | proposals/20261112T170301Z-7f3a.md | accepted | host: h | "
                 "authority: person direct\n"
                 "- 2026-11-12T17:05:00Z | topics/travel.md | added a preference | host: h | "
                 "authority: accepted proposal 20261112T170301Z-7f3a\n")
        self.assertEqual(flat(self.report()[1]["warnings"]), [])

    def test_pending_proposed_before_refusal_is_a_warning(self):
        self.put("proposals/20261112T170301Z-aaaa.md",
                 self.proposal(status="refused", extra="decided-at: 2026-11-12T18:00:00Z\n"))
        self.put("proposals/20261112T170500Z-bbbb.md", self.proposal(proposed_at="2026-11-12T17:05:00Z"))
        code, report = self.report()
        self.assertEqual(code, 0)
        self.assertTrue(any("proposed before that refusal" in w for w in flat(report["warnings"])))

    def test_lock_and_missing_final_line_break_are_notes(self):
        self.put(".me.lock", "examplehost 1.0 2026-11-12T17:03:01Z\n")
        self.put("journal.md", "- 2026-11-12T17:03:01Z | me.md | added an aim | host: h | authority: person direct")
        code, report = self.report()
        notes = flat(report["notes"])
        self.assertEqual(code, 0)
        self.assertTrue(any(n.startswith(".me.lock: the store lock exists") for n in notes), notes)
        self.assertTrue(any("does not end with a line break" in n for n in notes), notes)

    def test_badly_named_proposal_is_invalid_and_counts_as_refused(self):
        self.put("proposals/no-aisle.md", self.proposal(status="refused"))
        self.put("proposals/notes.txt", "not a proposal\n")
        self.put("proposals/20261112T180000Z-bbbb.md", self.proposal(proposed_at="2026-11-12T18:00:00Z"))
        code, report = self.report()
        self.assertEqual(code, 1)
        self.assertTrue(any("no-aisle.md: name must be" in e for e in flat(report["errors"])))
        warnings = flat(report["warnings"])
        self.assertTrue(any("same body as invalid proposal no-aisle.md" in w for w in warnings), warnings)
        self.assertTrue(any("notes.txt: ignored by hosts" in w for w in warnings), warnings)
        self.assertEqual(report["counts"]["proposals_invalid"], 1)

    def test_policy_rejects_non_standard_constants(self):
        self.put("policy.json", '{"state": "on", "x": NaN}\n')
        self.assertEqual(self.report()[1]["policy"]["state"], "off")

    def test_usage_errors_exit_2(self):
        self.assertEqual(run_lint(os.path.join(self._tmp.name, "missing"))[0], 2)
        self.assertEqual(subprocess.run([sys.executable, LINT], stderr=subprocess.PIPE).returncode, 2)


if __name__ == "__main__":
    unittest.main()
