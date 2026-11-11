# CLAUDE.md

Guidance for Claude Code (and other coding agents) working in this repository.

Agentic AI Workflow is a small Python command-line app, the Stackademy
assistant, that demonstrates OpenAI function calling driving an agentic
workflow: the model looks up courses in a MySQL database (`get_courses`) and
registers students (`register_course`), and the app chains those calls into a
conversation. It is teaching material for the FullStackWithLawrence YouTube
channel, so the code is meant to be read by students: keep it simple and
explicit.

Detailed know-how lives in the Agent Skills under `skills/` (symlinked to
`.claude/skills`). **Load `agentic-ai-workflow-development` first for any
change.** This file holds only what applies to nearly every task.

## Hard rules

1. **Never run git write commands.** "Write a git commit" means print the
   command as text. Never run `git commit`, `git add`, `git reset`, `git push`
   or anything else that changes the index or history. That includes
   `make release`, which commits and pushes. Format and authorship are in
   `agentic-ai-workflow-git-commits`.
2. **Never edit or print `.env`.** It holds the real OpenAI key and MySQL
   credentials. Read a setting's name from `.env.example` or
   `app/settings.py` instead.
3. **Run the tests yourself** after any change (`make test`, about 15
   seconds, in the Docker container). Never ask the user to re-run them. Report failures honestly,
   including pre-existing ones.
4. **Live, billable OpenAI calls are fine** during development. Some unit
   tests make them too, so every test run sends a few small requests.
5. **Never write to the MySQL database** outside a mocked test. The app
   connects as a read-only user to the MariaDB in its Docker container, and
   `make docker-init` resets it. Tests patch `pymysql.connect` or the
   `DatabaseConnection` methods; follow that pattern.
6. **The pre-commit hooks are the lint standard** (`make lint`), as in the
   other smarter-sh repositories. CI runs them on every file.
7. **This repository is public.** No API keys, tokens, passwords, private
   hostnames or personal data in code, tests, docs or skills.

## Repository map

| Path                            | Contents                                                                     |
| ------------------------------- | ---------------------------------------------------------------------------- |
| `app/agent.py`                  | Entry point (`python -m app.agent`): the interactive conversation loop       |
| `app/prompt.py`                 | Messages, `completion()` and `handle_function_call()`                        |
| `app/stackademy.py`             | `Stackademy`: the functions the model calls and their `tool_factory_*()`     |
| `app/database.py`               | `DatabaseConnection`: PyMySQL connection, cursor and query helpers           |
| `app/structured_outputs.py`     | Pydantic models for structured outputs                                       |
| `app/settings.py`               | Settings from environment variables / `.env`; fails fast when one is missing |
| `app/tests/`                    | `unittest` tests, one module per source module                               |
| `data/`                         | Example YAML manifests used in the course                                    |
| `doc/`                          | Contributor and course documentation                                         |
| `Dockerfile`                    | One image: the app and a MariaDB server that holds the course database       |
| `scripts/`                      | `create-course-database.sh` + `.sql`, copied from smarter-sh/stackademy      |
| `requirements/in/*.in`          | Pinned inputs; `requirements/*.txt` are compiled from them by pip-compile    |
| `.github/workflows/ci.yml`      | CI on pull requests: pre-commit, tests with coverage, Docker build           |
| `.github/workflows/release.yml` | Push to main, alpha, beta: CI, then semantic-release                         |
| `release.config.js`             | semantic-release: `scripts/bump_version.py`, CHANGELOG.md, tag               |
| `codecov.yml`                   | Codecov: coverage reported, not enforced                                     |
| `skills/`                       | Agent Skills, symlinked to `.claude/skills`                                  |

## Common commands

The app, its tests and its MariaDB course database run in one Docker
container, `agentic-ai-workflow`, which mounts `app/` and `pyproject.toml`.
There is no virtual environment to set up.

```bash
make docker-init                  # build, (re)create the container, create the database
make test                         # python -m unittest discover -s app/, in the container
make coverage                     # tests with a coverage report; copies out coverage.xml
make run                          # run the app interactively, in the container
make lint                         # every pre-commit hook on every file (pre-commit on PATH)
```

`make docker-init` replaces the container and resets the database; run it
after a change to the `Dockerfile` or the requirements. Values in `.env` can
be overridden on the command line, e.g. `make test MYSQL_HOST=127.0.0.1`. `make release` starts the
Release workflow on GitHub; never run it.

The host shell is zsh, which doesn't word-split variables: a file list in
`$FILES` reaches a command as one argument. Use `xargs`.

## Conventions

- **Pattern first.** Read the neighbouring code and copy its structure,
  naming, docstrings, logging and error handling.
- **Settings** come from `app/settings.py` only. Add a new one there (with a
  default, or a check that fails fast) and to `.env.example`.
- **Logging:** `logger = get_logger(__name__)` from `app.logging_config`,
  with %-style arguments (`logger.info("got %s", x)`), never f-strings. Never
  log the API key or a password.
- **Tests:** `unittest`, one test module per source module, mock the
  database and anything slow. Keep coverage from dropping.
- **Versions** are written by semantic-release (`scripts/bump_version.py`
  updates `app/__version__.py`, `pyproject.toml` and the `Dockerfile` label).
  Don't bump them by hand, and don't edit `CHANGELOG.md`.
- **Branches:** work goes to `alpha`, then a PR from `alpha` to `main`.

## Definition of done

- The change follows an existing pattern.
- Tests cover it, and you ran them.
- `make lint` passes.
- Public functions and classes have docstrings.
- Your summary says what changed, what you verified, and what you skipped.
