# Rules for this repository

This repository is **public**.

- Never name the commercial product this code is used in, its private
  repositories, its web site, or paths on the author's machines - not in
  files, file names, comments, commit messages, branch names, tags, issues or
  pull requests. Where the downstream application matters, call it "the host
  application".
- `tools/name_guard.py` enforces this: as a git hook
  (`git config core.hooksPath .githooks`) and in CI
  (`.github/workflows/name-guard.yml`). It holds only hashes of the forbidden
  names; never write a name into it or anywhere else here.
- If the check fires, rewrite the text; do not weaken or bypass the check.
