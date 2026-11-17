"""Safe file access inside one store (STORE.md S2.4, S2.7, S8).

Every path is store-relative and is checked against the store's layout before
use, so nothing here can reach outside the store. No symbolic link inside the
store is ever followed.
"""

import errno
import os
import re
import secrets
import socket
import stat
import time

from . import formats

O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_BINARY = getattr(os, "O_BINARY", 0)

# The only paths a host touches (S2, S8.2, S8.4).
_NAME = r"[a-z0-9][a-z0-9._-]{0,63}\.md"
_PATH_RE = re.compile(r"(?:me\.md|watches\.md|journal\.md|policy\.json|\.me\.lock"
                      r"|(?:topics|projects)/" + _NAME + r"|proposals/[^/\\\x00]+)")
LOCK = ".me.lock"


def location():
    """S1.1: $ME_HOME if it is set, ~/.me otherwise. An empty ME_HOME counts as unset."""
    home = os.environ.get("ME_HOME")
    if home:
        return os.path.abspath(os.path.expanduser(home))
    return os.path.join(os.path.expanduser("~"), ".me")


class Missing(Exception):
    """The file is not there, or is a link or not a regular file, which counts as not there (S2.4)."""

    def __init__(self, rel, why):
        Exception.__init__(self, why)
        self.rel, self.why = rel, why


class Locked(Exception):
    pass


class StoreFS:
    def __init__(self, root):
        self.root = root

    # --- paths ---

    def check(self, rel):
        if not _PATH_RE.fullmatch(rel) or rel.startswith("proposals/."):
            raise ValueError("not a store path: %r" % rel)
        return rel

    def abs(self, rel):
        return os.path.join(self.root, *self.check(rel).split("/"))

    def kind(self, rel):
        """'missing', 'link', 'file', or 'other', without following a link at any level."""
        parts = self.check(rel).split("/")
        path = self.root
        for index, part in enumerate(parts):
            path = os.path.join(path, part)
            try:
                mode = os.lstat(path).st_mode
            except FileNotFoundError:
                return "missing"
            except OSError:
                return "other"
            if stat.S_ISLNK(mode):
                return "link"
            if index < len(parts) - 1 and not stat.S_ISDIR(mode):
                return "other"
        return "file" if stat.S_ISREG(mode) else "other"

    def root_exists(self):
        return os.path.isdir(self.root)

    # --- reading ---

    def read(self, rel):
        """The bytes of a regular file. Raises Missing for a missing file, a link, or anything else."""
        kind = self.kind(rel)
        if kind == "missing":
            raise Missing(rel, "it does not exist")
        if kind == "link":
            raise Missing(rel, "it is a symbolic link, and hosts never follow links inside the store")
        if kind != "file":
            raise Missing(rel, "it is not a regular file")
        try:
            fd = os.open(self.abs(rel), os.O_RDONLY | O_NOFOLLOW | O_BINARY)
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                raise Missing(rel, "it does not exist")
            raise Missing(rel, "it cannot be read (%s)" % exc.strerror)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise Missing(rel, "it is not a regular file")
            chunks = []
            while True:
                chunk = os.read(fd, 1 << 20)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)
        finally:
            os.close(fd)

    def read_or_none(self, rel):
        try:
            return self.read(rel)
        except Missing as exc:
            if exc.why == "it does not exist":
                return None
            raise

    def listdir(self, folder):
        """(names of regular files, notices) in topics/, projects/ or proposals/. Never follows links."""
        path = os.path.join(self.root, folder)
        try:
            mode = os.lstat(path).st_mode
        except OSError:
            return [], []
        if stat.S_ISLNK(mode):
            return [], ["%s/ is a symbolic link, so it is ignored (S2.4)." % folder]
        if not stat.S_ISDIR(mode):
            return [], []
        names, notices = [], []
        for name in sorted(os.listdir(path)):
            if name.startswith("."):
                continue  # S2.2: hidden files, including temp files and locks
            try:
                mode = os.lstat(os.path.join(path, name)).st_mode
            except OSError:
                continue
            if stat.S_ISLNK(mode):
                notices.append("%s/%s is a symbolic link, so it is ignored (S2.4)." % (folder, name))
            elif stat.S_ISREG(mode):
                names.append(name)
        return names, notices

    # --- writing ---

    def _mkdirs(self, rel):
        parts = rel.split("/")[:-1]
        path = self.root
        for part in parts:
            path = os.path.join(path, part)
            try:
                os.mkdir(path, 0o700)  # S2.5
            except FileExistsError:
                if os.path.islink(path) or not os.path.isdir(path):
                    raise Missing(rel, "%s is not a plain folder" % part)

    def create(self, rel, data):
        """Create a new file exclusively (S6.2, S8.5). Raises FileExistsError if the name is taken."""
        self._mkdirs(rel)
        fd = os.open(self.abs(rel), os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW | O_BINARY, 0o600)
        try:
            _write_all(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)

    def replace(self, rel, change, attempts=5):
        """S8.4: read, write a temp file, read again and compare, rename. Call with the lock held.

        change(old_bytes_or_None) returns the new bytes, or None for no change.
        Returns (old, new); new is None when nothing changed."""
        if self.kind(rel) not in ("missing", "file"):
            raise Missing(rel, "it is a symbolic link or not a regular file, so the host will not replace it")
        self._mkdirs(rel)
        target = self.abs(rel)
        folder, name = os.path.split(target)
        for _ in range(attempts):
            old = self.read_or_none(rel)
            new = change(old)
            if new is None or new == old:
                return old, None
            tmp = os.path.join(folder, ".%s.%s.tmp" % (name, secrets.token_hex(4)))
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW | O_BINARY, 0o600)
            try:
                _write_all(fd, new)
                if old is not None and hasattr(os, "fchmod"):
                    # Keep the person's permissions on a file the host rewrites.
                    os.fchmod(fd, stat.S_IMODE(os.lstat(target).st_mode))
                os.fsync(fd)
            finally:
                os.close(fd)
            if self.read_or_none(rel) != old:
                os.unlink(tmp)  # a program that does not take the lock changed it; start again
                continue
            os.replace(tmp, target)
            return old, new
        raise Locked("%s kept changing while the host tried to write it" % rel)

    def remove(self, rel):
        if self.kind(rel) != "file":
            raise Missing(rel, "it is not a regular file")
        os.unlink(self.abs(rel))

    # --- the store lock (S8.2, S8.3) ---

    def lock(self, host, wait=None):
        wait = float(os.environ.get("THOU_LOCK_WAIT", "3")) if wait is None else wait
        token = secrets.token_hex(16)
        line = ("%s %s %s %s\n" % (token, formats.one_line(host), socket.gethostname(), formats.now())).encode("utf-8")
        deadline = time.monotonic() + wait
        path = os.path.join(self.root, LOCK)
        while True:
            try:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW | O_BINARY, 0o600)
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise Locked(
                        "Another host holds the store lock, so I made no change. If no host is writing, "
                        "for example after one stopped in the middle of a change, you can delete %s."
                        % os.path.join(self.root, LOCK))
                time.sleep(0.02 + secrets.randbelow(30) / 1000)
                continue
            try:
                _write_all(fd, line)
            finally:
                os.close(fd)
            return token

    def unlock(self, token):
        """Remove the lock only if it still holds this host's token (S8.2, S8.3)."""
        try:
            held = self.read(LOCK)
        except Missing:
            return
        if held.split(b" ", 1)[0] == token.encode("ascii"):
            os.unlink(os.path.join(self.root, LOCK))

    # --- the journal (S8.1) ---

    def journal(self, entry):
        """Append one entry in a single write. Returns False when it could not (S8.7)."""
        if self.kind("journal.md") not in ("missing", "file"):
            return False  # S2.4: never append to a link
        path = self.abs("journal.md")
        try:
            fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_APPEND | O_NOFOLLOW | O_BINARY, 0o600)
        except OSError:
            return False
        try:
            data = (entry + "\n").encode("utf-8")
            size = os.fstat(fd).st_size
            if size:
                if os.pread(fd, 1, size - 1) != b"\n":
                    data = b"\n" + data
            _write_all(fd, data)
            return True
        except OSError:
            return False
        finally:
            os.close(fd)


def _write_all(fd, data):
    view = memoryview(data)
    while view:
        view = view[os.write(fd, view):]
