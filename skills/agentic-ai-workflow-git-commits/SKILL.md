---
name: agentic-ai-workflow-git-commits
description: Use whenever the user asks you to "write a git commit" (or a commit message, or the git add) in the agentic-ai-workflow repo. Covers the never-execute rule, authorship, the multiple -m command format, conventional-commit types, and how thorough the body must be.
---

# Agentic AI Workflow Git Commits

## The rule: write, never execute

"Write a git commit", in any wording or tone, means **output the command as
text**. It never means run it.

- Never execute `git commit`, `git add`, `git reset`, `git restore --staged`,
  `git push`, `git tag`, `git stash`, `make release`, or any other command that
  writes to git. The user stages, commits and pushes.
- Read-only git commands (`git status`, `git diff`, `git log`) are fine.
- Don't volunteer commit messages. Write one only when asked.

## Authorship

You are the author. Lawrence McDaniel is the co-author.

- `--author="Claude <noreply@anthropic.com>"`
- The last `-m` is `Co-authored-by: Lawrence McDaniel <lpm0073@gmail.com>`.

## Command format

Exactly one `git commit` command in one code block:

```console
git commit --author="Claude <noreply@anthropic.com>" \
  -m "<type>(<scope>): <subject>" \
  -m "<body paragraph>" \
  -m "<body paragraph or bullet list>" \
  -m "Co-authored-by: Lawrence McDaniel <lpm0073@gmail.com>"
```

- One `-m` per paragraph. No heredoc, no `-F`, no `git add` in the same block.
- Avoid backticks, `$` and `!` inside the double quotes. The user's shell is
  zsh, where `!` triggers history expansion and aborts the command.
- Never write a CI skip instruction anywhere in the message (`[skip ci]`,
  `[ci skip]`, `[no ci]`, `skip-checks: true`), not even to describe one.
  GitHub would then start no workflows for the push.
- When asked for the `git add` too, write it as a separate code block with
  explicit paths.

## Subject line

`<type>(<scope>): <subject>`, checked by commitlint (`commitlint.config.js`)
and read by semantic-release (`release.config.js`) to version the release.

- **type:** `feat`, `fix`, `test`, `docs`, `refactor`, `perf`, `style`,
  `build`, `ci`, or `chore`. `feat` triggers a minor release, so reserve it
  for a truly new capability, such as a new tool the model can call. When in
  doubt, it is `fix`.
- **scope:** optional, the module the change centers on: `prompt`, `agent`,
  `stackademy`, `database`, `settings`, `docker`, `ci`, ...
- **subject:** imperative mood, lower case, no trailing period.
- **length:** the whole header must be 72 characters or fewer. Measure it:
  `printf %s "fix(prompt): ..." | wc -c`.
- `chore(release): ...` belongs to semantic-release. Never write it.

## Body

Write for a reviewer with no context: the problem first, then one bullet per
change naming files and functions and saying why, then the tests and what
they prove, then anything skipped or pending.

## Before writing

1. Run `git status` and `git diff --stat` (and `git diff` on anything unclear).
2. Ask which files belong to the commit if that's ambiguous.
3. Measure the header with `wc -c`.
