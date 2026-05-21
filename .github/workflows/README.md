# GitHub Actions Notifications

The `testsPython.yml` workflow can notify Slack, Discord, Microsoft Teams, Mailgun, and Twilio when the Python unit test job fails. It can also send manual test notifications or print dry-run payloads from the GitHub Actions UI.

The workflow calls `scripts/github_actions_notify.py`. The script uses only the Python standard library, so the GitHub Actions runner does not need to install vendor SDKs.

## Behavior

- Notifications are sent when `python-unit-tests` fails.
- The notification job uses `if: ${{ always() }}` so it still runs after a test failure.
- Each provider is optional. A provider is skipped when its required configuration or addressees are not configured.
- Each provider supports JSON arrays where multiple addressees make sense.
- Slack and Discord support target objects so mentions can be set per webhook destination.
- Notification failures are allowed to continue so a broken notification provider does not block CI.
- Dry-run output masks webhook URLs, email addresses, and phone numbers in logs.

## GitHub Secrets and Variables

Add secrets and variables from the repository settings:

1. Open the repository in GitHub.
2. Go to `Settings` -> `Secrets and variables` -> `Actions`.
3. Add sensitive values under `Secrets`.
4. Add non-sensitive values under `Variables`.

Treat webhook URLs, API keys, email addresses, phone numbers, Account SIDs, and Messaging Service SIDs as secrets. Dry-run logs mask these values, but GitHub Actions can still print workflow environment values that are stored as variables.

Use JSON arrays for multiple addressees:

```json
["first@example.com", "second@example.com"]
```

Provider addressee fields use JSON arrays so one workflow configuration can send to multiple destinations.

Slack and Discord use target objects so each webhook destination can have its own optional mentions:

```json
[
  {
    "url": "https://example.invalid/webhook",
    "mentions": ["<@U0123456789>", "<!channel>"]
  },
  {
    "url": "https://example.invalid/another-webhook"
  }
]
```

## Manual Testing

Open the `Actions` tab, select `Python Unit Tests`, choose `Run workflow`, then set `notification-mode`.

### `notify-on-failure`

Use `notify-on-failure` for normal workflow behavior. Notifications are sent only when the Python unit test job fails.

### `dry-run`

Use `dry-run` to print parsed addressee lists and payloads without sending notifications. This is the safest first test after adding configuration.

### `test-notification`

Use `test-notification` to send configured notifications even if the Python tests pass. Use this after dry-run output looks correct.

## Slack

Get credentials from Slack by creating or selecting a Slack app and enabling Incoming Webhooks:

- Slack Incoming Webhooks: https://api.slack.com/messaging/webhooks
- Slack GitHub Action docs: https://docs.slack.dev/tools/slack-github-action/

After you have webhook URLs, configure this secret:

| Type | Name | Example |
| --- | --- | --- |
| Secret | `SLACK_WEBHOOK_TARGETS_JSON` | `[{"url": "https://hooks.slack.com/services/T000/B000/XXX", "mentions": ["<@U0123456789>", "<!channel>"]}, {"url": "https://hooks.slack.com/services/T111/B111/YYY"}]` |

Each target object requires `url` and may include an optional `mentions` array.

Each Slack webhook is tied to the channel selected when the webhook is created, so a list of webhook URLs is the Slack addressee list.

## Discord

Get credentials by creating webhooks in the Discord channels that should receive alerts:

- Discord webhook resources: https://discord.com/developers/docs/resources/webhook
- Discord webhook guide: https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks

After you have webhook URLs, configure this secret:

| Type | Name | Example |
| --- | --- | --- |
| Secret | `DISCORD_WEBHOOK_TARGETS_JSON` | `[{"url": "https://discord.com/api/webhooks/111/aaa", "mentions": ["<@everyone>"]}, {"url": "https://discord.com/api/webhooks/222/bbb"}]` |

Each target object requires `url` and may include an optional `mentions` array.

Each Discord webhook is tied to one channel.

## Microsoft Teams

Get a Teams webhook URL from the Microsoft Teams Workflows app or from the incoming webhook option supported by your tenant:

- Teams incoming webhook setup: https://support.microsoft.com/en-US/Workflows/send-messages-in-teams-using-incoming-webhooks

After you have webhook URLs, configure this secret:

| Type | Name | Example |
| --- | --- | --- |
| Secret | `TEAMS_WEBHOOK_URLS_JSON` | `["https://example.webhook.office.com/webhookb2/...", "https://prod-00.westus.logic.azure.com/..."]` |

Each Teams webhook maps to the team, channel, or workflow destination selected during setup.

## Mailgun

Get credentials from Mailgun:

- Mailgun dashboard: https://app.mailgun.com/
- Mailgun API keys: https://app.mailgun.com/app/account/security/api_keys
- Mailgun sending domains: https://app.mailgun.com/app/sending/domains
- Mailgun Messages API: https://documentation.mailgun.com/docs/mailgun/api-reference/send/mailgun/messages

After you have an API key and a sending domain, configure:

| Type | Name | Example |
| --- | --- | --- |
| Secret | `MAILGUN_API_KEY` | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| Variable | `MAILGUN_DOMAIN` | `mg.example.com` |
| Secret | `MAILGUN_FROM_EMAIL` | `GitHub Actions <postmaster@mg.example.com>` |
| Secret | `MAILGUN_TO_EMAILS_JSON` | `["first@example.com", "second@example.com"]` |
| Variable <sup>[1]</sup> | `MAILGUN_API_BASE_URL` | `https://api.mailgun.net/v3` |

<sup>[1]</sup> `MAILGUN_API_BASE_URL` is optional. The default is `https://api.mailgun.net/v3`. Use `https://api.eu.mailgun.net/v3` for Mailgun EU domains.

## Twilio

Get credentials from Twilio:

- Twilio Console: https://console.twilio.com/
- Twilio API credentials: https://www.twilio.com/docs/iam/api
- Twilio Messaging API: https://www.twilio.com/docs/messaging/api/message-resource
- Twilio phone numbers: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming

After you have an Account SID, Auth Token, and a sending phone number or Messaging Service SID, configure:

| Type | Name | Example |
| --- | --- | --- |
| Secret | `TWILIO_ACCOUNT_SID` | `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| Secret | `TWILIO_AUTH_TOKEN` | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| Secret | `TWILIO_TO_PHONES_JSON` | `["+16045550123", "+12505550123"]` |
| Secret <sup>[1]</sup> | `TWILIO_FROM_PHONE` | `+16045550999` |
| Secret <sup>[1]</sup> | `TWILIO_MESSAGING_SERVICE_SID` | `MGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |

<sup>[1]</sup> Set either `TWILIO_FROM_PHONE` or `TWILIO_MESSAGING_SERVICE_SID`. SMS providers may charge for sent messages, phone numbers, carrier fees, and message segments.

## Example Dry-Run Configuration

For a safe dry run, configure personal addresses and phone numbers as secrets and non-sensitive routing values as variables.

Secrets:

```text
MAILGUN_FROM_EMAIL=GitHub Actions <postmaster@mg.example.com>
MAILGUN_TO_EMAILS_JSON=["first@example.com", "second@example.com"]
TWILIO_TO_PHONES_JSON=["+16045550123", "+12505550123"]
TWILIO_FROM_PHONE=+16045550999
```

Variables:

```text
MAILGUN_DOMAIN=mg.example.com
```

Then manually run `Python Unit Tests` with `notification-mode=dry-run`.

For webhook providers, the webhook URL is both the addressee and the credential, so store webhook lists as GitHub secrets before testing.
