# CI Notifications — Complete Testing Guide

## Overview & Total Time

**~60–75 minutes total.** Three natural stopping points are marked clearly.

---

## Part 1 — Gmail App Password

**⏱ ~10 min**

You need an App Password (not your regular Gmail password) because Google blocks direct
password auth for automated tools.

1. Go to [myaccount.google.com](https://myaccount.google.com) → **Security**
2. Ensure **2-Step Verification** is turned on (required for App Passwords)
3. Search for **"App Passwords"** in the search bar at the top
4. Click **App Passwords** → under "Select app" choose **Mail**, under "Select device" choose **Other** → type `GitHub Actions`
5. Click **Generate** — copy the 16-character password shown (spaces don't matter)
6. Save it somewhere safe — Google won't show it again

---

## Part 2 — Free Slack Workspace + Webhook

**⏱ ~15 min**

1. Go to **slack.com** → click **"Get started for free"**
2. Sign up with your email → name the workspace anything (e.g. `CI Test`)
3. Skip inviting teammates
4. Once inside your workspace, go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
5. Name it `GitHub Actions`, select your workspace → **Create App**
6. On the left sidebar → **Incoming Webhooks** → toggle **Activate Incoming Webhooks** to On
7. Scroll down → **Add New Webhook to Workspace** → select any channel (e.g. `#general`) → **Allow**
8. Copy the **Webhook URL** (starts with `https://hooks.slack.com/services/...`)

---

## Part 3 — Add GitHub Secrets

**⏱ ~10 min**

In your forked repo on GitHub: **Settings → Secrets and variables → Actions → New repository secret**

Add all of these secrets:

### Notification secrets

| Secret name | Value |
|---|---|
| `SLACK_WEBHOOK_URL` | The URL from Part 2 |
| `MAIL_USERNAME` | Your Gmail address (e.g. `you@gmail.com`) |
| `MAIL_PASSWORD` | The 16-char app password from Part 1 |
| `NOTIFY_EMAIL` | Where to receive emails — can be same as `MAIL_USERNAME` |

### OpenAI secrets

| Secret name      | Value                                      |
|------------------|--------------------------------------------|
| `OPENAI_API_KEY` | Your OpenAI API key (starts with `sk-`)    |

> Find it at **platform.openai.com → API keys**. `OPENAI_API_ORGANIZATION` is **not needed** — it's passed by the workflow but not used by the code.

### MySQL secrets (dummy values are fine — tests mock the database)

| Secret name | Value |
|---|---|
| `MYSQL_HOST` | `localhost` |
| `MYSQL_USER` | `test_user` |
| `MYSQL_PASSWORD` | `password` |
| `MYSQL_DATABASE` | `test` |

> `MYSQL_PORT` does **not** need to be set — the custom action defaults it to `3306`.

### Codecov (optional)

The workflow uploads coverage reports to Codecov. You have two options:

**Option A — Skip it (quickest):** The custom action at `.github/actions/tests/python/action.yml`
has `fail_ci_if_error: true` on the Codecov upload step. Change it to `false` and the upload
will fail silently without blocking the workflow. No account needed.

**Option B — Set it up free:** Go to **codecov.io** → Sign in with GitHub → add your repo →
copy the token → add it as `CODECOV_TOKEN`. Codecov is a legitimate service (owned by Sentry)
used by major open source projects. Free for public repos.

---

## 🛑 STOP 1 — Good place to pause (~35 min in)

Everything is configured. You have all credentials in place. Pick this back up at Part 4 when ready.

---

## Part 4 — Create a Branch and Push Your Changes

**⏱ ~5 min**

In your terminal, from the project root:

```bash
git checkout -b feature/ci-notifications
git add .github/workflows/testsPython.yml
git commit -m "feat: add failure notifications to Python unit tests workflow"
git push -u origin feature/ci-notifications
```

Your changes are now on GitHub on a feature branch. The workflow will **not** trigger yet —
the `push` trigger only watches `main` and `next`. That's fine — we'll trigger it manually next.

---

## Part 5 — Test 1: Verify the Happy Path (Tests Pass)

**⏱ ~5 min**

This confirms the workflow runs cleanly before introducing any failures.

1. Go to your repo on GitHub → **Actions** tab
2. Click **Python Unit Tests** in the left sidebar
3. Click **Run workflow** (top right) → select branch `feature/ci-notifications` → click **Run workflow**
4. Wait ~2–3 minutes for it to complete

**What to verify:**

- Both jobs (`python-unit-tests` and `notifications`) show green ✅
- Click the `notifications` job → click **Write job summary** step → you should see a `✅ Python Tests Passed` table
- No Slack message, no email, no GitHub issue created (correct — only fires on failure)
- Click the **Summary** tab on the run — you'll see the markdown summary rendered there

---

## 🛑 STOP 2 — Good place to pause (~40 min in)

Basic workflow confirmed working. All setup validated. Pick up at Part 6 to test failure notifications.

---

## Part 6 — Test 2: Introduce a Bug to Trigger Failure Notifications

**⏱ ~10 min**

Open `app/tests/test_utils.py` and make this one-line change on line 22:

```python
# Before (original):
self.assertIn("\033[", result)

# After (intentional break):
self.assertIn("THIS_WILL_NEVER_MATCH", result)
```

This test has no external dependencies (no database, no OpenAI key) so it will fail
cleanly and predictably — ideal for controlled testing.

Then commit and push:

```bash
git add app/tests/test_utils.py
git commit -m "test: intentional break to test CI notifications"
git push
```

Trigger the workflow manually (**Actions → Python Unit Tests → Run workflow → your branch**).

**What to verify:**

- `python-unit-tests` job goes red ❌
- `notifications` job still runs (proof the `if: always()` fix works)
- Click **Write job summary** → see `❌ Python Tests Failed` table
- Check your Slack channel — message should arrive within ~30 seconds of the job finishing
- Check your email inbox — may take 1–2 minutes
- Go to **Issues** tab in your repo — a new issue titled `❌ Tests failed on refs/heads/feature/ci-notifications (...)` should appear with a `bug` label

---

## Part 7 — Test 3: Fix the Bug and Verify Auto-Close

**⏱ ~5 min**

Use `git revert` to undo the break commit — no manual file editing needed:

```bash
git revert HEAD --no-edit
git push
```

This creates a new commit that undoes the previous one, restoring the test to its original state.

Trigger the workflow manually again.

**What to verify:**

- Both jobs green ✅
- Go to **Issues** tab — the issue from Part 6 should now be **closed**
- Click into it — you should see a comment: `✅ Tests are passing again as of commit ... Closing.`

---

## Part 8 — Test 4: Parameterized Email Recipient

**⏱ ~5 min**

This tests the `workflow_dispatch` input — the "optionally parameterize the addressee"
part of the assignment requirement.

Re-apply the break by reverting the revert:

```bash
git revert HEAD --no-edit
git push
```

Then:

1. **Actions → Python Unit Tests → Run workflow**
2. You'll see an input field: **"Recipient email(s) for failure notification"**
3. Enter a different address (a teammate, another account, or comma-separated list)
4. Verify the email arrives at the address you typed, not `NOTIFY_EMAIL`

Revert again to restore passing tests and confirm issue auto-closes:

```bash
git revert HEAD --no-edit
git push
```

---

## Part 9 — Test 5: Verify Graceful Degradation (No Slack Secret)

**⏱ ~5 min**

This validates that the workflow doesn't break for contributors who haven't configured Slack —
the guard `secrets.SLACK_WEBHOOK_URL != ''` should cause the step to be silently skipped.

- **Step 1:** Go to **Settings → Secrets and variables → Actions** → find `SLACK_WEBHOOK_URL` → delete it
- **Step 2:** Re-apply the break:

```bash
git revert HEAD --no-edit
git push
```

- **Step 3:** Trigger the workflow manually

**What to verify:**

- `notifications` job completes successfully ✅ (not failed)
- The **Notify Slack on failure** step shows as **skipped** (greyed out in the Actions UI)
- Email notification still fires normally
- GitHub issue still gets created normally
- Job summary still shows ❌

- **Step 4:** Revert to fix the tests and confirm issue auto-closes:

```bash
git revert HEAD --no-edit
git push
```

- **Step 5:** Re-add the `SLACK_WEBHOOK_URL` secret if you want Slack notifications restored

---

## 🛑 STOP 3 — Everything fully exercised (~80 min in)

All features validated end-to-end. You're done.

---

## Summary of What You've Built

| Feature | Trigger | Where to see it |
|---|---|---|
| Job summary | Every run | Actions → run → Summary tab |
| Slack notification | Test failure | Your Slack channel |
| Email notification | Test failure | Inbox (or typed address on manual run) |
| GitHub issue | Test failure | Repo Issues tab |
| Auto-close issue | Tests pass after failure | Closed issue with comment |

---

## Pre-Flight Checklist

Before starting, confirm all of these:

- [ ] Repo is **your fork** (not the upstream FullStackWithLawrence repo) — secrets and Actions only exist on your fork
- [ ] Branch is pushed to **your fork**, not upstream
- [ ] All 4 secrets are added under your fork's Settings
- [ ] `bug` label exists in your repo's Issues → Labels (it's a GitHub default, should already be there)
- [ ] Gmail 2-Step Verification is on (required for App Passwords to work)
- [ ] Slack workspace is created and webhook URL is copied before adding the secret
