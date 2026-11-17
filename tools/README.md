# me-lint

`me_lint.py` checks that a me.md store follows the v0.1 file format. It is one file, Python 3.9 or newer, standard library only.

## What it checks

- The store is present when `me.md` exists. With no `me.md` it reports "absent" and stops. Absence is a normal state, not an error. A symlinked `me.md` also means absent, with a warning.
- `policy.json`: whether memory is on or off, and why. A symlink, invalid JSON, or a member that appears twice means off. It warns when `spec` is not `"0.1"`, because v0.1 hosts must not write to that store. It notes when `spec` is missing.
- Layout: file names in `topics/`, `projects/` and `proposals/` (a `.md` file in `proposals/` with a bad name is an invalid proposal, not an ignored file); UTF-8 without a BOM; no symlinks inside the store. It never follows a symlink. It never reads `.git/` or unknown top-level entries. It notes a leftover `.me.lock`.
- `watches.md`: counts the top-level list items outside fenced code blocks.
- Proposals: file name and id, front matter grammar, duplicate keys, required keys and empty values, `status` values, `target`, times, and a non-empty body. The status comes only from the front matter. A `status:` line in the body is reported as a note and otherwise ignored.
- Refusals: a pending proposal whose normalized body equals a refused proposal's body, for any target, is an error if it was proposed after the refusal. A pending proposal with the same body as an invalid proposal is a warning, because hosts treat an invalid proposal as refused.
- `journal.md`: every line that starts with `- ` is an entry and must match the entry grammar. Other lines are ignored. Every accepted or refused proposal should have a decision entry, and every accepted one a content entry. A missing entry is a warning, because the person may have decided by editing the file by hand.

Times and digits are ASCII only. Names that hosts ignore are warnings. Anything that breaks the format is an error.

## What it does not prove

It is not a conformance test of a host. It cannot tell you that a host honors `policy.json`, resists injection, asks before writing, takes the store lock, or writes a journal entry for each change it made. It only checks that the files a host wrote look right. A clean report does not mean a host conforms.

## Run it

```
python3 tools/me_lint.py ~/.me
python3 tools/me_lint.py ~/.me --json
```

Human output has one line per finding: `ERROR`, `WARN` or `NOTE`, then the path, then the message. Exit 0 means no errors. Exit 1 means errors. Exit 2 means a usage error, such as a path that is not a directory.

It only reads the store. It never writes to it.

## Run the tests

```
python3 -m unittest discover -s tools -p 'test_*.py'
```

The tests run every store in `conformance/fixtures/`. Each fixture has a `store/` directory and an `expect.json`. The fixtures are synthetic. Symlink, BOM and invalid UTF-8 cases are built in a temp directory at test time, so none are committed.
