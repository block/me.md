"""Unit tests for thou-py. Every test uses a temporary store."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "..", "tools"))

from thou_host import formats  # noqa: E402
from thou_host.host import Host, HostError  # noqa: E402
from thou_host.storefs import location  # noqa: E402

import thou_lint  # noqa: E402

PROPOSAL = """---
status: pending
target: topics/travel.md
proposed-by: examplehost 1.0
proposed-at: 2026-11-12T17:03:01Z
basis: You asked twice.
---

Prefer aisle seats.
"""


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, "store")
        os.mkdir(self.root)
        self.write("me.md", "I like blue.\n")
        self.host = Host(self.root, agent="test")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def path(self, rel):
        return os.path.join(self.root, *rel.split("/"))

    def write(self, rel, text, binary=False):
        path = self.path(rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(text if binary else text.encode("utf-8"))

    def read(self, rel):
        with open(self.path(rel), "rb") as handle:
            return handle.read()

    def lint(self):
        report = thou_lint.lint(self.root)
        self.assertEqual(report.errors, [], report.errors)
        return report

    def code(self, fn, *args, **kwargs):
        with self.assertRaises(HostError) as ctx:
            fn(*args, **kwargs)
        return ctx.exception.code


class Location(unittest.TestCase):
    def test_me_home_wins(self):
        old = dict(os.environ)
        try:
            os.environ["ME_HOME"] = "/tmp/x-store"
            self.assertEqual(location(), "/tmp/x-store")
            os.environ["ME_HOME"] = ""
            os.environ["HOME"] = "/tmp/x-home"
            self.assertEqual(location(), "/tmp/x-home/.me")
        finally:
            os.environ.clear()
            os.environ.update(old)


class Policy(StoreTest):
    OFF = ['{"state": "off"}', "{not json", '{"state": "ON"}', "{}", "",
           '{"state": "on", "state": "off"}', '{"state": "on", "x": {"a": 1, "a": 2}}', "[]", '"on"',
           '{"state": "on", "n": NaN}']

    def test_off_variants_hide_everything(self):
        self.write("topics/t.md", "CANARY-T\n")
        for text in self.OFF:
            self.write("policy.json", text)
            answer = json.dumps([self.host.mount(), self.host.list(), self.host.recall(["topics/t.md"]),
                                 self.host.pending()])
            self.assertNotIn("I like blue", answer, text)
            self.assertNotIn("CANARY-T", answer, text)
            self.assertEqual(self.host.mount()["memory"], "off", text)
            self.assertEqual(self.code(self.host.propose, "me.md", "x", "y"), "memory_off")

    def test_symlinked_policy_is_off(self):
        other = os.path.join(self.tmp, "p.json")
        with open(other, "w") as handle:
            handle.write('{"state": "on"}')
        os.symlink(other, self.path("policy.json"))
        self.assertEqual(self.host.mount()["memory"], "off")

    def test_unknown_member_keeps_on(self):
        self.write("policy.json", '{"state": "on", "note": "x"}')
        self.assertEqual(self.host.mount()["memory"], "on")

    def test_unsupported_spec_blocks_writes_but_not_off(self):
        self.write("proposals/20261112T170301Z-7f3a.md", PROPOSAL)
        for spec in ("9.0", "0.2", "0.10"):
            self.write("policy.json", '{"state": "on", "spec": "%s"}' % spec)
            self.assertIs(self.host.mount()["writable"], False)
            self.assertEqual(self.code(self.host.propose, "me.md", "x", "y"), "unsupported_spec")
            self.assertEqual(self.code(self.host.decide, "20261112T170301Z-7f3a", "accept"), "unsupported_spec")
            self.assertEqual(self.code(self.host.edit, "me.md", "append", text="x"), "unsupported_spec")
        self.assertEqual(self.host.policy("off")["memory"], "off")
        self.assertEqual(json.loads(self.read("policy.json")), {"state": "off", "spec": "0.10"})
        self.assertEqual(self.code(self.host.policy, "on"), "unsupported_spec")

    def test_switch_while_off_keeps_members_and_journals(self):
        self.write("policy.json", '{"state": "off", "keep": [1, 2], "spec": "0.1"}')
        answer = self.host.policy("on")
        self.assertEqual(answer["memory"], "on")
        self.assertEqual(json.loads(self.read("policy.json")), {"state": "on", "keep": [1, 2], "spec": "0.1"})
        self.assertIn("turned memory on", answer["journal"][0])
        self.host.policy("off")
        self.assertEqual(self.read("journal.md").count(b"\n"), 2)
        self.lint()

    def test_invalid_policy_is_replaced(self):
        self.write("policy.json", '{"state": "on", "state": "on"}')
        self.host.policy("on")
        self.assertEqual(json.loads(self.read("policy.json")), {"state": "on", "spec": "0.1"})

    def test_off_with_no_policy_creates_it_with_spec(self):
        self.host.policy("off")
        self.assertEqual(json.loads(self.read("policy.json")), {"state": "off", "spec": "0.1"})

    def test_no_store_is_absent_and_untouched(self):
        shutil.rmtree(self.root)
        host = Host(self.root)
        self.assertEqual(host.mount()["memory"], "absent")
        for call in (lambda: host.propose("me.md", "x", "y"), lambda: host.policy("off"),
                     lambda: host.edit("me.md", "append", text="x")):
            self.assertEqual(self.code(call), "absent")
        self.assertFalse(os.path.exists(self.root))


class Recall(StoreTest):
    def test_traversal_links_and_hidden_files(self):
        outside = os.path.join(self.tmp, "outside.md")
        with open(outside, "w") as handle:
            handle.write("CANARY-OUT\n")
        os.makedirs(self.path("topics"))
        os.symlink(outside, self.path("topics/link.md"))
        self.write("topics/.hidden.md", "CANARY-HIDDEN\n")
        paths = ["../outside.md", "topics/../../outside.md", outside, "topics/link.md", "topics/.hidden.md",
                 "journal.md", "policy.json", "topics/Travel.md"]
        answer = self.host.recall(paths)
        self.assertEqual(answer["files"], [])
        self.assertEqual(len(answer["skipped"]), len(paths))
        self.assertNotIn("CANARY", json.dumps(answer))
        self.assertNotIn("CANARY", json.dumps(self.host.list()))

    def test_linked_me_md_is_absent(self):
        other = os.path.join(self.tmp, "real.md")
        with open(other, "w") as handle:
            handle.write("CANARY-ME\n")
        os.remove(self.path("me.md"))
        os.symlink(other, self.path("me.md"))
        answer = self.host.mount()
        self.assertEqual(answer["memory"], "absent")
        self.assertNotIn("CANARY", json.dumps(answer))

    def test_watches_only_on_request(self):
        self.write("watches.md", "- CANARY-W\n")
        self.assertNotIn("CANARY-W", json.dumps(self.host.recall(["watches.md"])))
        self.assertIn("CANARY-W", json.dumps(self.host.recall(["watches.md"], "watches")))

    def test_off_mid_session(self):
        self.write("topics/t.md", "CANARY-T\n")
        self.assertIn("CANARY-T", json.dumps(self.host.recall(["topics/t.md"])))
        self.write("policy.json", '{"state": "off"}')
        self.assertNotIn("CANARY-T", json.dumps(self.host.recall(["topics/t.md"])))

    def test_list_ignores_bad_names_and_says_so(self):
        self.write("topics/travel.md", "x\n")
        self.write("topics/My Notes.md", "x\n")  # macOS folders are case-insensitive, so not Travel.md
        answer = self.host.list()
        self.assertEqual(answer["topics"], ["travel.md"])
        self.assertTrue(any("My Notes.md" in n for n in answer["notices"]))


class Proposals(StoreTest):
    def test_propose_writes_one_valid_file(self):
        answer = self.host.propose("topics/travel.md", "Prefer aisle seats.", "You asked twice.")
        self.assertEqual(os.listdir(self.path("proposals")), [answer["proposal"] + ".md"])
        self.assertEqual(self.read("me.md"), b"I like blue.\n")
        self.assertEqual(self.lint().counts.get("proposals_pending"), 1)
        self.assertEqual(self.host.pending()["proposals"][0]["body"], "Prefer aisle seats.\n")

    def test_quoting_odd_values(self):
        answer = self.host.propose("me.md", "x", '"quoted" start', agent="a | b (c)")
        pending = self.host.pending()["proposals"][0]
        self.assertEqual(pending["basis"], '"quoted" start')
        self.assertNotIn("|", pending["proposed-by"])
        self.assertTrue(answer["proposal"])
        self.lint()

    def test_refusals_hold_for_any_target_and_spacing(self):
        self.write("proposals/20261112T170301Z-aaaa.md", PROPOSAL.replace("pending", "refused"))
        self.write("proposals/20261112T170301Z-bbbb.md",
                   PROPOSAL.replace("status: pending", "Status: Refused").replace("aisle", "window"))
        for body in ("Prefer   aisle seats.", "  Prefer aisle\nseats. ", "Prefer window seats."):
            for target in ("me.md", "projects/x.md"):
                self.assertEqual(self.code(self.host.propose, target, body, "b"), "refused")
        self.assertEqual(len(os.listdir(self.path("proposals"))), 2)

    def test_status_in_body_is_content(self):
        self.write("proposals/20261112T170301Z-aaaa.md", PROPOSAL.replace("Prefer", "status: accepted\nPrefer"))
        self.assertEqual(len(self.host.pending()["proposals"]), 1)

    def test_invalid_files_are_listed(self):
        self.write("proposals/bad-name.md", PROPOSAL)
        self.write("proposals/20261112T170301Z-cccc.md", PROPOSAL.replace("basis", "Basis"))
        self.write("proposals/notes.txt", "ignored")
        answer = self.host.pending()
        self.assertEqual(sorted(i["file"] for i in answer["invalid"]),
                         ["proposals/20261112T170301Z-cccc.md", "proposals/bad-name.md"])
        self.assertEqual(answer["proposals"], [])


class Decide(StoreTest):
    def setUp(self):
        StoreTest.setUp(self)
        self.write("proposals/20261112T170301Z-7f3a.md", PROPOSAL)

    def test_accept_order_and_receipt(self):
        answer = self.host.decide("20261112T170301Z-7f3a", "accept")
        self.assertEqual(answer["applied"], "added")
        self.assertEqual(self.read("topics/travel.md"), b"Prefer aisle seats.\n")
        self.assertIn(b"status: accepted\ndecided-at: ", self.read("proposals/20261112T170301Z-7f3a.md"))
        journal = self.read("journal.md").decode().splitlines()
        self.assertEqual(journal, answer["journal"])
        self.assertIn("| proposals/20261112T170301Z-7f3a.md | accepted |", journal[0])
        self.assertIn("authority: accepted proposal 20261112T170301Z-7f3a", journal[1])
        self.assertEqual(self.lint().warnings, [])
        self.assertEqual(self.code(self.host.decide, "20261112T170301Z-7f3a", "accept"), "not_pending")
        self.assertEqual(self.read("topics/travel.md"), b"Prefer aisle seats.\n")

    def test_refuse(self):
        answer = self.host.decide("20261112T170301Z-7f3a", "refuse")
        self.assertEqual((answer["status"], answer["applied"], len(answer["journal"])), ("refused", None, 1))
        self.assertFalse(os.path.exists(self.path("topics/travel.md")))
        self.lint()

    def test_crlf_target_without_final_break(self):
        self.write("topics/travel.md", b"one\r\ntwo", binary=True)
        self.write("proposals/20261112T170301Z-7f3a.md", PROPOSAL.replace("Prefer aisle seats.", "a\nb"))
        self.host.decide("20261112T170301Z-7f3a", "accept")
        self.assertEqual(self.read("topics/travel.md"), b"one\r\ntwo\r\na\r\nb\r\n")

    def test_already_applied_is_not_added_twice(self):
        self.write("topics/travel.md", "x\nPrefer aisle seats.\n")
        answer = self.host.decide("20261112T170301Z-7f3a", "accept")
        self.assertEqual(answer["applied"], "already")
        self.assertEqual(self.read("topics/travel.md"), b"x\nPrefer aisle seats.\n")
        self.assertEqual(len(answer["journal"]), 2)

    def test_unknown_key_line_kept(self):
        text = PROPOSAL.replace("basis:", 'x-note:   "keep  me"\n# a comment\nbasis:')
        self.write("proposals/20261112T170301Z-7f3a.md", text)
        self.host.decide("20261112T170301Z-7f3a", "accept")
        after = self.read("proposals/20261112T170301Z-7f3a.md").decode()
        self.assertIn('x-note:   "keep  me"\n# a comment\n', after)
        self.assertTrue(after.endswith("---\n\nPrefer aisle seats.\n"))

    def test_crlf_proposal_keeps_crlf(self):
        self.write("proposals/20261112T170301Z-7f3a.md", PROPOSAL.replace("\n", "\r\n"))
        self.host.decide("20261112T170301Z-7f3a", "accept")
        after = self.read("proposals/20261112T170301Z-7f3a.md")
        self.assertNotIn(b"\n", after.replace(b"\r\n", b""))
        self.lint()

    def test_duplicate_status_is_invalid(self):
        text = PROPOSAL.replace("status: pending", "status: pending\nstatus: accepted")
        self.write("proposals/20261112T170301Z-7f3a.md", text)
        self.assertEqual(self.code(self.host.decide, "20261112T170301Z-7f3a", "accept"), "invalid_proposal")
        self.assertEqual(self.read("proposals/20261112T170301Z-7f3a.md").decode(), text)
        self.assertFalse(os.path.exists(self.path("topics/travel.md")))

    def test_foreign_lock_is_left_alone(self):
        self.write(".me.lock", "someone-elses-token-123 otherhost 2026-11-12T17:03:01Z\n")
        os.environ["THOU_LOCK_WAIT"] = "0.2"
        try:
            with self.assertRaises(HostError) as ctx:
                self.host.decide("20261112T170301Z-7f3a", "accept")
        finally:
            del os.environ["THOU_LOCK_WAIT"]
        self.assertEqual(ctx.exception.code, "locked")
        self.assertTrue(any(".me.lock" in n for n in ctx.exception.notices))
        self.assertEqual(self.read(".me.lock"), b"someone-elses-token-123 otherhost 2026-11-12T17:03:01Z\n")

    def test_revise_then_accept(self):
        self.host.revise("20261112T170301Z-7f3a", "Prefer exit rows.")
        self.host.decide("20261112T170301Z-7f3a", "accept")
        self.assertEqual(self.read("topics/travel.md"), b"Prefer exit rows.\n")

    def test_journal_link_means_no_receipt(self):
        other = os.path.join(self.tmp, "j.md")
        open(other, "w").close()
        os.symlink(other, self.path("journal.md"))
        answer = self.host.decide("20261112T170301Z-7f3a", "accept")
        self.assertEqual(answer["journal"], [])
        self.assertTrue(any("no receipt" in n for n in answer["notices"]))
        self.assertEqual(os.path.getsize(other), 0)


class Edit(StoreTest):
    def test_replace_keeps_other_bytes(self):
        data = b"I like blue.\r\n\x01odd\xe2\x80\xa8line\r\nkeep\r\n"
        self.write("me.md", data, binary=True)
        self.host.edit("me.md", "replace", old="keep", new="kept\nnow")
        self.assertEqual(self.read("me.md"), data.replace(b"keep", b"kept\r\nnow"))
        self.assertIn("person direct", self.read("journal.md").decode())
        self.lint()

    def test_replace_errors(self):
        self.write("me.md", "a\na\n")
        self.assertEqual(self.code(self.host.edit, "me.md", "replace", old="a", new="b"), "ambiguous")
        self.assertEqual(self.code(self.host.edit, "me.md", "replace", old="z", new="b"), "no_match")
        self.assertEqual(self.code(self.host.edit, "../x", "append", text="b"), "bad_path")
        self.assertEqual(self.code(self.host.edit, "journal.md", "append", text="b"), "bad_path")

    def test_append_creates_topic(self):
        answer = self.host.edit("topics/travel.md", "append", text="I prefer aisle seats.")
        self.assertIn("created the file", answer["journal"][0])
        self.assertEqual(oct(os.stat(self.path("topics")).st_mode & 0o777), "0o700")
        self.assertEqual(oct(os.stat(self.path("topics/travel.md")).st_mode & 0o777), "0o600")


class Forget(StoreTest):
    def test_forget_lines_and_applied_proposal(self):
        self.write("proposals/20261112T170301Z-7f3a.md", PROPOSAL)
        self.host.decide("20261112T170301Z-7f3a", "accept")
        self.write("proposals/20261112T170301Z-bbbb.md", PROPOSAL.replace("pending", "refused")
                   .replace("Prefer aisle seats.", "Prefer aisle seats. Also more."))
        answer = self.host.forget("topics/travel.md", "Prefer aisle seats.")
        self.assertEqual(answer["removed"], 1)
        self.assertEqual(self.read("topics/travel.md"), b"")
        self.assertFalse(os.path.exists(self.path("proposals/20261112T170301Z-7f3a.md")))
        notices = " ".join(answer["notices"])
        self.assertIn("model provider", notices)
        self.assertIn("20261112T170301Z-bbbb", notices)
        self.assertNotIn("Prefer aisle", json.dumps(self.host.recall(["topics/travel.md"])))
        self.assertEqual(len(self.read("journal.md").decode().splitlines()), 4)

    def test_forget_only_whole_lines(self):
        self.write("me.md", "x blue\nblue\nblue")
        answer = self.host.forget("me.md", "blue")
        self.assertEqual(answer["removed"], 2)
        self.assertEqual(self.read("me.md"), b"x blue\n")
        self.assertEqual(self.code(self.host.forget, "me.md", "nothing"), "no_match")


class Formats(unittest.TestCase):
    def test_append_rules(self):
        self.assertEqual(formats.appended(None, "a\r\nb\n\n"), b"a\nb\n")
        self.assertEqual(formats.appended(b"", "a"), b"a\n")
        self.assertEqual(formats.appended(b"x", "a"), b"x\na\n")
        self.assertIsNone(formats.appended(b"a\n", "a"))
        self.assertIsNone(formats.appended(b"x\r\na\r\n", "a"))
        self.assertEqual(formats.appended(b"xa\n", "a"), b"xa\na\n")

    def test_normalize(self):
        self.assertEqual(formats.normalize(" é  x\n"), "é x")


class Concurrency(StoreTest):
    def test_two_processes_accept_same_target(self):
        driver = os.path.join(os.path.dirname(HERE), "thou_driver.py")
        env = {"PATH": os.environ.get("PATH", ""), "HOME": self.tmp, "ME_HOME": self.root}
        for round_ in range(15):
            ids = []
            for n in range(2):
                pid = "20261112T170301Z-r%02dn%d" % (round_, n)
                self.write("proposals/%s.md" % pid, PROPOSAL.replace("Prefer aisle seats.", "Body %d-%d" % (round_, n)))
                ids.append(pid)
            procs = [subprocess.Popen([sys.executable, driver], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      env=env, text=True) for _ in ids]
            for proc in procs:
                proc.stdin.write('{"id": 1, "op": "mount"}\n')
                proc.stdin.flush()
                proc.stdout.readline()
            for proc, pid in zip(procs, ids):
                proc.stdin.write(json.dumps({"id": 2, "op": "decide", "proposal": pid, "decision": "accept"}) + "\n")
            for proc in procs:
                proc.stdin.close()
            answers = [json.loads(proc.stdout.readline()) for proc in procs]
            for proc in procs:
                proc.stdout.close()
                proc.wait(10)
            self.assertTrue(all(a["ok"] for a in answers), answers)
            text = self.read("topics/travel.md").decode()
            for n in range(2):
                self.assertEqual(text.count("Body %d-%d\n" % (round_, n)), 1)
        self.assertFalse(os.path.exists(self.path(".me.lock")))
        self.assertEqual(self.lint().warnings, [])


if __name__ == "__main__":
    unittest.main()
