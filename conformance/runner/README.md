# thou conformance runner

`thou_conform.py` drives a host through the engine-level part of the black-box tests in [HOST.md](../../HOST.md) (T1 to T17). It talks to the host through a driver, as [DRIVER.md](../DRIVER.md) describes. Then it checks the store the host left behind. It is one file. It needs Python 3.9 or newer and the standard library only. It runs on macOS and Linux.

## What it does

- It asks the driver for `host`. It runs the tests for the claimed level and the levels below it.
- Each test gets fresh temporary directories: a `HOME`, a `TMPDIR`, the four XDG directories, and a store. The driver starts with a minimal environment: `PATH` and those directories. The runner never passes on the real `HOME` or `ME_HOME`.
- Each test plants canaries: unique strings in `me.md`, topics, proposals and so on. After the test, the runner searches the test `HOME`, `TMPDIR` and XDG directories for them. A canary there is a copy of store content (H1.3, H5.2).
- For a host that claims only the Reader level, the runner compares the store byte for byte before and after each session (H0.2).
- Every driver answer is checked: valid JSON, the request id echoed, only the error codes DRIVER.md lists, the fields each operation needs.
- It checks journals and proposals with [thou-lint](../../tools/README.md), which it imports.
- It kills every driver it starts. Each answer has a time limit (10 s by default).

Each test ends as pass, fail or not run. A failure names the requirement (for example `S6.8` or `H1.5`) and says what was wrong.

Besides T1 to T17, the runner has four extra tests: `X1` (deciding twice, `revise`, a symbolic-link target), `X2` (proposal file names), `X3` (what `list` leaves out) and `X4` (`journal.md` is a symbolic link).

## Run it

```
python3 conformance/runner/thou_conform.py --host "python3 path/to/thou_driver.py"
```

Options:

| Option | Meaning |
|---|---|
| `--host CMD` | The driver command. The runner splits it with `shlex`. |
| `--second-host CMD` | A second, unrelated host. T9 uses it as host B. T15 also runs a cross-host race. Without it, T9 uses the same host twice and says so. |
| `--repeat N` | How many races T15 runs (default 50). |
| `--only T3,T6` | Run only these tests. |
| `--json` | Print machine-readable results. |
| `--keep` | Keep the temporary directories, and print where they are. |
| `--timeout S` | Seconds to wait for each answer (default 10). |

Exit code: 0 if every test that ran passed. 1 if a test failed. 2 for a usage error, or if the driver could not be started or did not answer `host`.

The driver runs in the directory where you start the runner, so a relative command works.

## What a pass means

A pass means the host's code passed the engine-level tests. It is not a conformance claim by itself. A claim needs a release, a level, and the tests the runner cannot run (see below). See [H0.3](../../HOST.md#conformance-levels).

A pass also does not show that the host's driver and the host's real interface share the same code. DRIVER.md asks for that. A reviewer has to check it.

If the host says `"enforcement": "instruction"`, the runner reports it. The claim must then say "by instruction" (H0.3, H6.4).

## What it cannot show

The runner has no model. These parts are reported as not run:

- **T4**, Injection: instruction-shaped text in the store must never make an agent call a tool.
- **T18**, Briefing: a briefing is produced by an agent.
- **T2**, the last step: what the person says now wins over `me.md` (H2.3).
- **T7**, the model's part: asking for `watches.md` only in a briefing or when asked. The runner checks the engine's `purpose` rule.
- **T8**, the model's part: stating a preference only by implication, and then proposing it. The runner checks the `propose` operation.
- Choosing what to recall (H2.1): the agent reads a topic only when the task makes it relevant.

Tests above the claimed level are also reported as not run.

Other limits:

- The runner reads files and answers. It does not see which files a host opened. A host could read a file and not show it. The canary checks catch what shows up in answers or in the test directories.
- T15 is a race. Many passes make a failure unlikely. They do not prove there is none.
- Some checks look only at the bytes in the store, for example the `.me.lock` file. They cannot see inside the host.

## Run the runner's own tests

```
python3 -m unittest discover -s conformance/runner -p 'test_*.py'
```

`fakes/fake_host.py` is a small host written only as a test fixture. It is not a host to use. In its correct mode it passes. Each `--break` flag adds a deliberate bug, and the matching test must fail. This shows that the checks can fail.

## Agent adapter (planned)

The model-level tests need an agent with a model. Adding them is planned. The idea:

- An adapter starts an agent against the host, with a test store and a mock `send` tool.
- It gives the agent a short task, and reads the host's tool calls and the transcript.
- T4 plants several instruction-shaped payloads and checks that the mock tool is never called.
- T2 asks for the opposite of a preference in `me.md` and checks the agent follows the person.
- T7 and T8 check what the agent recalls and proposes.
- T18 checks that a briefing has the five parts, a coverage receipt, and writes nothing.
- Results use the same pass, fail and not-run format. A host's claim lists both runs.

Nothing here is built yet.
