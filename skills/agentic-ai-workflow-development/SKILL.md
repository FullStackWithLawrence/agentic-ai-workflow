---
name: agentic-ai-workflow-development
description: Start here for any change to the agentic-ai-workflow repository (the Stackademy assistant, a Python CLI demonstrating OpenAI function calling against a MySQL database). Gives the rules, how the app is put together, how to run and test it, and an index of the narrower agentic-ai-workflow-* skills.
---

# Agentic AI Workflow Development

## How the app works

`python -m app.agent` starts a loop in `app/agent.py`. Each user message goes
to `completion()` in `app/prompt.py`, which:

1. appends the message to the module-level `messages` list (the whole
   conversation, starting with the system prompt),
2. calls the OpenAI Chat Completions API with the tool definitions built by
   `Stackademy.tool_factory_*()` and `tool_choice` from `LLM_TOOL_CHOICE`,
3. for each tool call the model makes, runs `handle_function_call()`, which
   dispatches to `stackademy_app` (`app/stackademy.py`), and appends the
   result as a tool message,
4. calls the API again so the model can answer from the tool results, and
   returns the response plus the names of the functions called.

`agent.py` uses those names to choose the next prompt, and stops on
"Goodbye!" or an exit phrase. `Stackademy` reads and writes MySQL through
`DatabaseConnection` (`app/database.py`). `app/settings.py` reads `.env`
at import time and raises `ConfigurationException` if the OpenAI key or a
MySQL setting is missing, so importing anything under `app` needs a complete
`.env`.

## Rules

The hard rules in `CLAUDE.md` apply. In short: never run git write commands,
never touch `.env`, run the tests yourself, never write to the real database,
the pre-commit hooks are the lint standard, and the repository is public.

## Adding a tool (a function the model can call)

1. Implement it as a method of `Stackademy`, with a docstring and logging.
2. Add a `tool_factory_<name>()` method beside `tool_factory_get_courses()`
   and `tool_factory_register()` that returns its tool definition, and pass
   it in the `tools=[...]` lists of `completion()` in `app/prompt.py`.
3. Dispatch it in `handle_function_call()` (`app/prompt.py`).
4. Mention it in the system prompt if the model needs guidance on when to
   use it.
5. Test the method (database mocked) in `app/tests/test_stackademy.py`, and the
   dispatch in `app/tests/test_prompt.py`.

## Testing

```bash
source venv/bin/activate
make test                                   # all tests, about 10 seconds
python -m unittest app.tests.test_prompt    # one module
make coverage                               # with a coverage report
```

- Mock the database: `patch("app.database.pymysql.connect")`, or
  `patch.object(self.app.db, "execute_query", return_value=...)`. Look at
  `app/tests/test_database.py` and `app/tests/test_stackademy.py`.
- Mock OpenAI with `patch("app.prompt.openai...")` when the test is about your
  code rather than the model. A few tests call the real API; that is allowed.
- `prompt.messages` is module state shared by tests in one process. Reset
  or patch it if a test depends on the conversation's contents.

## Narrower skills

| Skill                             | Use it when                                  |
| --------------------------------- | -------------------------------------------- |
| `agentic-ai-workflow-git-commits` | You've been asked to write a commit message. |
