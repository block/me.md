#!/usr/bin/env python3
"""The conformance driver for thou-py (conformance/DRIVER.md).

One process is one session. Reads one JSON request per line on stdin and
writes one JSON response per line on stdout.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from thou_host.host import Host, HostError  # noqa: E402

_OPS = {
    "host": lambda h, r: h.host(),
    "mount": lambda h, r: h.mount(),
    "list": lambda h, r: h.list(),
    "recall": lambda h, r: h.recall(r.get("paths"), r.get("purpose", "task")),
    "pending": lambda h, r: h.pending(),
    "propose": lambda h, r: h.propose(r.get("target"), r.get("body"), r.get("basis"), r.get("agent")),
    "decide": lambda h, r: h.decide(r.get("proposal"), r.get("decision"), r.get("agent")),
    "revise": lambda h, r: h.revise(r.get("proposal"), r.get("body"), r.get("agent")),
    "edit": lambda h, r: h.edit(r.get("path"), r.get("action"), r.get("text"), r.get("old"), r.get("new"),
                                r.get("agent")),
    "forget": lambda h, r: h.forget(r.get("path"), r.get("text"), r.get("agent")),
    "policy": lambda h, r: h.policy(r.get("state"), r.get("agent")),
}


def handle(host, line):
    try:
        request = json.loads(line)
    except ValueError:
        return {"id": None, "ok": False, "error": "bad_request", "message": "The request is not JSON."}
    if not isinstance(request, dict):
        return {"id": None, "ok": False, "error": "bad_request", "message": "The request is not a JSON object."}
    rid = request.get("id")
    op = _OPS.get(request.get("op"))
    if op is None:
        return {"id": rid, "ok": False, "error": "unsupported_op", "message": "thou-py does not support %r."
                % (request.get("op"),)}
    try:
        answer = op(host, request)
    except HostError as exc:
        out = {"id": rid, "ok": False, "error": exc.code, "message": exc.message}
        if exc.notices:
            out["notices"] = exc.notices
        return out
    out = {"id": rid, "ok": True}
    out.update({k: v for k, v in answer.items() if not (k == "notices" and not v)})
    return out


def main():
    host = Host(agent="driver")
    for line in sys.stdin:
        if not line.strip():
            continue
        sys.stdout.write(json.dumps(handle(host, line), ensure_ascii=False) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
