"""Tests for the conformance runner. They prove that the runner can fail.

The fake host in fakes/fake_host.py is a test fixture, not a host. In its
correct mode every engine-level test must pass. Each `--break` mode is a
deliberate bug, and the matching test must fail.

Run: python3 -m unittest discover -s conformance/runner -p 'test_*.py'
"""

import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import thou_conform  # noqa: E402

FAKE = "%s %s" % (sys.executable, os.path.join(HERE, "fakes", "fake_host.py"))


def run(args="", only=None, repeat=8, second=None):
    runner = thou_conform.Runner(FAKE + (" " + args if args else ""), second, repeat=repeat)
    return runner.run(set(only) if only else None)


def by_id(result):
    return dict((t["id"], t) for t in result["tests"])


# broken mode -> tests that must fail
BROKEN = [
    ("write_when_absent", "T1"),
    ("copy_to_cache", "T2"),
    ("read_when_off", "T3"),
    ("loose_policy", "T3"),
    ("policy_cache", "T3"),
    ("follow_symlinks", "T6"),
    ("watches_leak", "T7"),
    ("ignore_refusals", "T9"),
    ("self_approve", "T10"),
    ("ignore_spec", "T11"),
    ("no_policy_journal", "T12"),
    ("rewrite_journal", "T13"),
    ("overwrite_not_append", "T13"),
    ("stale_cache", "T14"),
    ("no_notice_forget", "T14"),
    ("journal_content", "T14"),
    ("no_lock", "T15"),
    ("lock_remove_foreign", "T15"),
    ("torn_journal", "T15"),
    ("rewrite_crlf", "T16"),
    ("drop_unknown_keys", "T16"),
    ("decide_invalid", "T17"),
    ("accept_twice", "X1"),
    ("list_hidden", "X3"),
]


class CorrectMode(unittest.TestCase):
    def test_correct_fake_passes_everything_it_runs(self):
        result = run(second=FAKE + " --name otherhost")
        tests = by_id(result)
        for tid, t in tests.items():
            if t["status"] == "fail":
                self.fail("%s failed: %s" % (tid, t["failures"]))
        self.assertTrue(result["ok"])
        for tid in ("T4", "T18"):
            self.assertEqual(tests[tid]["status"], "not_run")
        self.assertEqual(result["summary"]["failed"], 0)
        self.assertGreaterEqual(result["summary"]["passed"], 18)
        self.assertIn("Last step", tests["T2"]["not_run_parts"][0])
        # the cross-host path ran with a different second host name
        self.assertEqual(result["second_host"]["name"], "otherhost")

    def test_without_second_host_t9_says_so(self):
        result = run(only=["T9"])
        self.assertEqual(by_id(result)["T9"]["status"], "pass")
        self.assertTrue(any("same host" in n for n in by_id(result)["T9"]["notes"]))


class BrokenModes(unittest.TestCase):
    pass


def make_test(mode, tid):
    def test(self):
        result = run("--break " + mode, only=[tid])
        t = by_id(result)[tid]
        self.assertEqual(t["status"], "fail", "%s did not catch %s" % (tid, mode))
        self.assertFalse(result["ok"])
        for failure in t["failures"]:
            self.assertTrue(failure["req"])
            self.assertTrue(failure["message"])
    return test


for _mode, _tid in BROKEN:
    setattr(BrokenModes, "test_%s_is_caught_by_%s" % (_mode, _tid), make_test(_mode, _tid))


class Levels(unittest.TestCase):
    def test_reader_runs_only_reader_tests(self):
        result = run("--level reader")
        tests = by_id(result)
        for tid in ("T1", "T2", "T3", "T5", "T6", "T7", "X3"):
            self.assertEqual(tests[tid]["status"], "pass", (tid, tests[tid]["failures"]))
        for tid in ("T8", "T12", "T15", "X1"):
            self.assertEqual(tests[tid]["status"], "not_run")
            self.assertIn("above the level", tests[tid]["reason"])
        self.assertTrue(result["ok"])

    def test_proposer_runs_proposer_tests(self):
        result = run("--level proposer")
        tests = by_id(result)
        for tid in ("T1", "T3", "T8", "T9", "T10", "T11", "X2"):
            self.assertEqual(tests[tid]["status"], "pass", (tid, tests[tid]["failures"]))
        self.assertEqual(tests["T12"]["status"], "not_run")

    def test_reader_that_writes_to_the_store_is_caught(self):
        result = run("--level reader --break touch_store", only=["T2"])
        failures = by_id(result)["T2"]["failures"]
        self.assertTrue(any(f["req"] == "H0.2" for f in failures), failures)


class DriverChecks(unittest.TestCase):
    def test_a_driver_that_cannot_start_fails_cleanly(self):
        runner = thou_conform.Runner("/nonexistent/driver-command")
        result = runner.run()
        self.assertTrue(result["preflight_failures"])
        self.assertFalse(result["ok"])

    def test_a_driver_that_lies_about_ids_is_caught(self):
        script = ("import sys, json\n"
                  "for line in sys.stdin:\n"
                  "    r = json.loads(line)\n"
                  "    print(json.dumps({'id': 99, 'ok': True, 'name': 'x', 'version': '1', 'spec': '0.1',"
                  " 'level': 'reader', 'enforcement': 'code'}), flush=True)\n")
        path = os.path.join(HERE, "fakes", "_liar.py")
        with open(path, "w") as handle:
            handle.write(script)
        try:
            runner = thou_conform.Runner("%s %s" % (sys.executable, path))
            result = runner.run()
            self.assertTrue(result["preflight_failures"])
            self.assertTrue(any("id" in m for m in result["preflight_failures"]))
        finally:
            os.unlink(path)

    def test_a_silent_driver_times_out_and_is_killed(self):
        path = os.path.join(HERE, "fakes", "_silent.py")
        with open(path, "w") as handle:
            handle.write("import sys, time\ntime.sleep(60)\n")
        try:
            runner = thou_conform.Runner("%s %s" % (sys.executable, path), timeout=1.0)
            result = runner.run()
            self.assertTrue(result["preflight_failures"])
        finally:
            os.unlink(path)


class Cli(unittest.TestCase):
    def test_json_output_and_exit_codes(self):
        script = os.path.join(HERE, "thou_conform.py")
        ok = subprocess.run([sys.executable, script, "--host", FAKE, "--only", "T1,T7", "--json"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        data = json.loads(ok.stdout)
        self.assertEqual([t["id"] for t in data["tests"]], ["T1", "T7"])
        bad = subprocess.run([sys.executable, script, "--host", FAKE + " --break read_when_off", "--only", "T3"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        self.assertEqual(bad.returncode, 1)
        self.assertIn("FAIL", bad.stdout.decode())
        usage = subprocess.run([sys.executable, script, "--host", FAKE, "--only", "T99"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        self.assertEqual(usage.returncode, 2)


if __name__ == "__main__":
    unittest.main()
