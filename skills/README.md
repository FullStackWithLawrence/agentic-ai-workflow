# Agent Skills

This folder holds the [Agent Skills](https://agentskills.io/specification) for
working on this repository with an AI coding agent such as Claude Code. They
are developer tooling, like the `Makefile`; the app never loads them.

| Skill                             | Use it when                                  |
| --------------------------------- | -------------------------------------------- |
| `agentic-ai-workflow-development` | You're making any change. Start here.        |
| `agentic-ai-workflow-git-commits` | You've been asked to write a commit message. |

Claude Code looks for project skills in `.claude/skills/`, which is a
symlink to this folder (`ln -s ../skills .claude/skills`). Each skill is a
folder with a `SKILL.md` whose frontmatter `description` tells the agent when
to load it.

Review changes here as carefully as changes to CI: an agent follows these
instructions without asking. Keep secrets out; this repository is public.
