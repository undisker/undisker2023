#!/usr/bin/env python3
"""Refuse names that must never appear in this public repository.

The names are not written here: the list holds the SHA-256 of each name
(lower case, letters only) and its length. Text is reduced the same way and
every window of that length is hashed and compared, so a name is caught in
any case, inside identifiers, paths and URLs, and split by punctuation.

  name_guard.py --staged            staged changes (pre-commit hook)
  name_guard.py --message FILE      a commit message (commit-msg hook)
  name_guard.py --range A..B        added lines and messages of commits (CI)
  name_guard.py --tree              every tracked file at HEAD

Exit status 1 if a name is found. To add a name, append its hash and length
to FORBIDDEN; never write the name itself into this repository.
"""
import hashlib, re, subprocess, sys

FORBIDDEN = [
    (6, "18097b758252dcbe27d6e30ed2c72add9da1d0e4b7ff09f908dd295ceb877407"),
]


def _letters(text):
    return "".join(ch for ch in text.lower() if "a" <= ch <= "z")


def _windows(s, length):
    for i in range(len(s) - length + 1):
        yield s[i:i + length]


def find(text, binary=False):
    """Text is reduced to its letters, so a name split by punctuation is
    still found. In binary data that would join random bytes into words, so
    there only unbroken runs of letters are searched."""
    hits = []
    if binary:
        runs = re.findall(r"[a-z]+", text.lower())
    else:
        runs = [_letters(text)]
    for length, digest in FORBIDDEN:
        if any(hashlib.sha256(w.encode()).hexdigest() == digest
               for run in runs for w in _windows(run, length)):
            hits.append(length)
    return hits


def git(*args):
    return subprocess.run(["git"] + list(args), stdout=subprocess.PIPE,
                          check=True).stdout.decode("utf-8", "replace")


def added_lines(diff):
    out, path = [], "?"
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else line[4:]
            out.append((path, path))  # the file name itself
        elif line.startswith("+") and not line.startswith("+++"):
            out.append((path, line[1:]))
    return out


def added_text(diff):
    """(path, text, is_binary) for every added line of a --text diff."""
    out = []
    for where, text in added_lines(diff):
        out.append((where, text, "\0" in text))
    return out


def main(argv):
    found = []
    if not argv or argv[0] == "--staged":
        for where, text, binary in added_text(git("diff", "--cached", "-U0", "--no-color", "--text")):
            if find(text, binary):
                found.append("staged change in " + where)
    elif argv[0] == "--message":
        if find(open(argv[1], encoding="utf-8", errors="replace").read()):
            found.append("commit message")
    elif argv[0] == "--range":
        rng = argv[1]
        for sha in git("rev-list", rng).split():
            if find(git("log", "-1", "--format=%B", sha)):
                found.append("message of " + sha[:10])
            for where, text, binary in added_text(git("show", "--format=", "-U0", "--no-color", "--text", sha)):
                if find(text, binary):
                    found.append("%s in %s" % (sha[:10], where))
    elif argv[0] == "--tree":
        for path in git("ls-files", "-z").split("\0"):
            if not path:
                continue
            if find(path):
                found.append("file name " + path)
                continue
            try:
                data = open(path, "rb").read()
            except OSError:
                continue
            if find(data.decode("latin-1"), binary=b"\0" in data[:8000]):
                found.append(path)
    else:
        print(__doc__)
        return 2
    for f in sorted(set(found)):
        print("name_guard: forbidden name in " + f, file=sys.stderr)
    if found:
        print("name_guard: this repository is public; describe the product generically "
              "(see CLAUDE.md)", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
