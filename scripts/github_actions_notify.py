#!/usr/bin/env python3
"""Send GitHub Actions test-result notifications to configured vendors."""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


USER_AGENT = "agentic-ai-workflow-github-actions-notifier/1.0"


class NotificationError(Exception):
    """Raised when a notification provider cannot complete its work."""


@dataclass(frozen=True)
class NotificationContext:
    """GitHub Actions context used to build notification messages."""

    repository: str
    workflow: str
    run_id: str
    run_attempt: str
    run_url: str
    ref_name: str
    sha: str
    actor: str
    event_name: str
    test_result: str
    notification_test: bool
    dry_run: bool

    @property
    def short_sha(self) -> str:
        return self.sha[:7] if self.sha else "unknown"

    @property
    def should_notify(self) -> bool:
        return self.dry_run or self.notification_test or self.test_result == "failure"

    @property
    def mode(self) -> str:
        if self.dry_run:
            return "dry-run"
        if self.notification_test:
            return "test"
        if self.test_result == "failure":
            return "failure"
        return "none"

    @property
    def title(self) -> str:
        if self.dry_run:
            return "GitHub Actions notification dry run"
        if self.notification_test:
            return "GitHub Actions test notification"
        if self.test_result == "failure":
            return "Python unit tests failed"
        return "Python unit tests completed"

    @property
    def subject(self) -> str:
        return f"{self.title}: {self.repository}"

    @property
    def message(self) -> str:
        return "\n".join(
            [
                self.title,
                f"Repository: {self.repository}",
                f"Workflow: {self.workflow}",
                f"Result: {self.test_result}",
                f"Branch: {self.ref_name}",
                f"Commit: {self.short_sha}",
                f"Actor: {self.actor}",
                f"Event: {self.event_name}",
                f"Run attempt: {self.run_attempt}",
                f"Run: {self.run_url}",
            ]
        )

    @property
    def sms_message(self) -> str:
        return (
            f"{self.title}: {self.repository} "
            f"{self.ref_name}@{self.short_sha} result={self.test_result}. "
            f"Run: {self.run_url}"
        )


@dataclass(frozen=True)
class WebhookTarget:
    """Webhook destination with optional provider-specific mentions."""

    url: str
    mentions: tuple[str, ...] = ()


def getenv(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip() or default


def truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def read_json_list(name: str) -> list[str]:
    """Read a JSON list from an environment variable."""

    raw = getenv(name)
    if raw:
        try:
            values = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise NotificationError(f"{name} must be a JSON list") from exc
        if not isinstance(values, list):
            raise NotificationError(f"{name} must be a JSON list")
        cleaned = [str(value).strip() for value in values if str(value).strip()]
        if len(cleaned) != len(values):
            raise NotificationError(f"{name} cannot contain empty values")
        return cleaned

    return []


def read_webhook_targets(
    targets_name: str,
) -> list[WebhookTarget]:
    """Read webhook targets with optional mentions."""

    raw = getenv(targets_name)
    if not raw:
        return []

    try:
        values = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise NotificationError(f"{targets_name} must be a JSON list of objects") from exc

    if not isinstance(values, list):
        raise NotificationError(f"{targets_name} must be a JSON list of objects")

    targets = []
    for index, value in enumerate(values, start=1):
        if not isinstance(value, dict):
            raise NotificationError(f"{targets_name}[{index}] must be an object")

        url = str(value.get("url", "")).strip()
        if not url:
            raise NotificationError(f"{targets_name}[{index}].url is required")

        mentions = value.get("mentions", [])
        if mentions is None:
            mentions = []
        if not isinstance(mentions, list):
            raise NotificationError(f"{targets_name}[{index}].mentions must be a JSON list")

        cleaned_mentions = [str(mention).strip() for mention in mentions if str(mention).strip()]
        if len(cleaned_mentions) != len(mentions):
            raise NotificationError(f"{targets_name}[{index}].mentions cannot contain empty values")

        targets.append(WebhookTarget(url=url, mentions=tuple(cleaned_mentions)))

    return targets


def mask_value(value: str, kind: str) -> str:
    if not value:
        return ""

    if kind == "url":
        parsed = urllib.parse.urlparse(value)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/<masked>"
        return "<masked-url>"

    if kind == "sensitive_url":
        return "<masked-url>"

    if kind == "email":
        if "<" in value and ">" in value:
            value = value[value.find("<") + 1 : value.rfind(">")].strip()
        if "@" not in value:
            return "<masked-email>"
        name, domain = value.split("@", 1)
        visible = name[:1] if name else "*"
        return f"{visible}***@{domain}"

    if kind == "sensitive_email":
        if "<" in value and ">" in value:
            value = value[value.find("<") + 1 : value.rfind(">")].strip()
        if "@" not in value:
            return "<masked-email>"
        name, _domain = value.split("@", 1)
        visible = name[:1] if name else "*"
        return f"{visible}***@<masked-domain>"

    if kind == "phone":
        digits = "".join(character for character in value if character.isdigit())
        suffix = digits[-4:] if len(digits) >= 4 else "****"
        return f"***{suffix}"

    if len(value) <= 8:
        return "<masked>"
    return f"{value[:4]}...{value[-4:]}"


def masked_list(values: list[str], kind: str) -> list[str]:
    return [mask_value(value, kind) for value in values]


def mask_mailgun_url(api_base_url: str) -> str:
    parsed = urllib.parse.urlparse(api_base_url)
    if parsed.scheme and parsed.netloc:
        base_path = parsed.path.rstrip("/")
        return f"{parsed.scheme}://{parsed.netloc}{base_path}/<masked-domain>/messages"
    return "<masked-mailgun-url>"


def masked_webhook_targets(targets: list[WebhookTarget]) -> list[dict[str, Any]]:
    return [
        {
            "url": mask_value(target.url, "url"),
            "mentions": list(target.mentions),
        }
        for target in targets
    ]


def print_json(label: str, payload: Any) -> None:
    print(label)
    print(json.dumps(payload, indent=2, sort_keys=True))


def http_post_json(url: str, payload: dict[str, Any]) -> tuple[int, str]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    return send_request(request)


def http_post_form(
    url: str,
    form_values: list[tuple[str, str]],
    username: str,
    password: str,
) -> tuple[int, str]:
    auth = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(form_values).encode("utf-8"),
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    return send_request(request)


def send_request(request: urllib.request.Request) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise NotificationError(f"HTTP {exc.code}: {body[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise NotificationError(f"Request failed: {exc.reason}") from exc


def send_webhook_notifications(
    provider: str,
    urls: list[str],
    payload: dict[str, Any],
    ctx: NotificationContext,
    url_mask_kind: str = "url",
) -> None:
    if not urls:
        print(f"{provider}: skipped, no webhook URLs configured")
        return

    print(f"{provider}: parsed addressees: {masked_list(urls, url_mask_kind)}")
    for index, url in enumerate(urls, start=1):
        masked_url = mask_value(url, url_mask_kind)
        if ctx.dry_run:
            print_json(f"{provider}: dry-run payload for addressee {index} ({masked_url})", payload)
            continue
        status, body = http_post_json(url, payload)
        print(f"{provider}: sent to addressee {index} ({masked_url}), status {status}, response {body[:200]}")


def send_targeted_webhook_notifications(
    provider: str,
    targets: list[WebhookTarget],
    ctx: NotificationContext,
    payload_builder: Callable[[WebhookTarget], dict[str, Any]],
) -> None:
    if not targets:
        print(f"{provider}: skipped, no webhook targets configured")
        return

    print_json(f"{provider}: parsed addressees", masked_webhook_targets(targets))
    for index, target in enumerate(targets, start=1):
        payload = payload_builder(target)
        masked_url = mask_value(target.url, "url")
        if ctx.dry_run:
            print_json(f"{provider}: dry-run payload for addressee {index} ({masked_url})", payload)
            continue
        status, body = http_post_json(target.url, payload)
        print(f"{provider}: sent to addressee {index} ({masked_url}), status {status}, response {body[:200]}")


def prepend_mentions(message: str, mentions: tuple[str, ...]) -> str:
    if not mentions:
        return message
    return f"{' '.join(mentions)}\n{message}"


def notify_slack(ctx: NotificationContext) -> None:
    targets = read_webhook_targets("SLACK_WEBHOOK_TARGETS_JSON")

    def build_payload(target: WebhookTarget) -> dict[str, Any]:
        return {"text": prepend_mentions(ctx.message, target.mentions)}

    send_targeted_webhook_notifications("Slack", targets, ctx, build_payload)


def notify_discord(ctx: NotificationContext) -> None:
    targets = read_webhook_targets("DISCORD_WEBHOOK_TARGETS_JSON")

    def build_payload(target: WebhookTarget) -> dict[str, Any]:
        return {"content": prepend_mentions(ctx.message, target.mentions)}

    send_targeted_webhook_notifications("Discord", targets, ctx, build_payload)


def build_teams_adaptive_card(ctx: NotificationContext) -> dict[str, Any]:
    facts = [
        {"title": "Repository", "value": ctx.repository},
        {"title": "Workflow", "value": ctx.workflow},
        {"title": "Result", "value": ctx.test_result},
        {"title": "Branch", "value": ctx.ref_name},
        {"title": "Commit", "value": ctx.short_sha},
        {"title": "Actor", "value": ctx.actor},
        {"title": "Event", "value": ctx.event_name},
        {"title": "Run attempt", "value": ctx.run_attempt},
    ]
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": ctx.title,
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True,
            },
            {
                "type": "FactSet",
                "facts": facts,
            },
        ],
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "Open workflow run",
                "url": ctx.run_url,
            }
        ],
    }


def notify_teams(ctx: NotificationContext) -> None:
    urls = read_json_list("TEAMS_WEBHOOK_URLS_JSON")
    payload = build_teams_adaptive_card(ctx)
    send_webhook_notifications("Microsoft Teams", urls, payload, ctx, "sensitive_url")


def notify_mailgun(ctx: NotificationContext) -> None:
    recipients = read_json_list("MAILGUN_TO_EMAILS_JSON")
    if not recipients:
        print("Mailgun: skipped, no email recipients configured")
        return

    domain = getenv("MAILGUN_DOMAIN")
    from_email = getenv("MAILGUN_FROM_EMAIL")
    api_key = getenv("MAILGUN_API_KEY")
    api_base_url = getenv("MAILGUN_API_BASE_URL", "https://api.mailgun.net/v3").rstrip("/")

    missing = []
    if not domain:
        missing.append("MAILGUN_DOMAIN")
    if not from_email:
        missing.append("MAILGUN_FROM_EMAIL")
    if not ctx.dry_run and not api_key:
        missing.append("MAILGUN_API_KEY")
    if missing:
        raise NotificationError(f"Mailgun missing required configuration: {', '.join(missing)}")

    form_values = [
        ("from", from_email),
        ("subject", ctx.subject),
        ("text", ctx.message),
    ]
    form_values.extend(("to", recipient) for recipient in recipients)

    print(f"Mailgun: parsed addressees: {masked_list(recipients, 'email')}")
    if ctx.dry_run:
        payload = {
            "from": mask_value(from_email, "sensitive_email"),
            "to": masked_list(recipients, "email"),
            "subject": ctx.subject,
            "text": ctx.message,
            "url": mask_mailgun_url(api_base_url),
        }
        print_json("Mailgun: dry-run payload", payload)
        return

    url = f"{api_base_url}/{urllib.parse.quote(domain, safe='')}/messages"
    status, body = http_post_form(url, form_values, "api", api_key)
    print(f"Mailgun: sent to {len(recipients)} recipients, status {status}, response {body[:200]}")


def notify_twilio(ctx: NotificationContext) -> None:
    recipients = read_json_list("TWILIO_TO_PHONES_JSON")
    if not recipients:
        print("Twilio: skipped, no phone recipients configured")
        return

    account_sid = getenv("TWILIO_ACCOUNT_SID")
    auth_token = getenv("TWILIO_AUTH_TOKEN")
    from_phone = getenv("TWILIO_FROM_PHONE")
    messaging_service_sid = getenv("TWILIO_MESSAGING_SERVICE_SID")

    missing = []
    if not ctx.dry_run and not account_sid:
        missing.append("TWILIO_ACCOUNT_SID")
    if not ctx.dry_run and not auth_token:
        missing.append("TWILIO_AUTH_TOKEN")
    if not from_phone and not messaging_service_sid:
        missing.append("TWILIO_FROM_PHONE or TWILIO_MESSAGING_SERVICE_SID")
    if missing:
        raise NotificationError(f"Twilio missing required configuration: {', '.join(missing)}")

    endpoint_sid = account_sid or "<TWILIO_ACCOUNT_SID>"
    url = f"https://api.twilio.com/2010-04-01/Accounts/{urllib.parse.quote(endpoint_sid, safe='')}/Messages.json"

    print(f"Twilio: parsed addressees: {masked_list(recipients, 'phone')}")
    for index, recipient in enumerate(recipients, start=1):
        form_values = [
            ("To", recipient),
            ("Body", ctx.sms_message),
        ]
        if messaging_service_sid:
            form_values.append(("MessagingServiceSid", messaging_service_sid))
        else:
            form_values.append(("From", from_phone))

        if ctx.dry_run:
            payload = {
                "to": mask_value(recipient, "phone"),
                "body": ctx.sms_message,
            }
            if messaging_service_sid:
                payload["messaging_service_sid"] = mask_value(messaging_service_sid, "generic")
            else:
                payload["from"] = mask_value(from_phone, "phone")
            print_json(f"Twilio: dry-run payload for recipient {index}", payload)
            continue

        status, body = http_post_form(url, form_values, account_sid, auth_token)
        print(
            "Twilio: sent to recipient "
            f"{index} ({mask_value(recipient, 'phone')}), status {status}, response {body[:200]}"
        )


def build_context() -> NotificationContext:
    return NotificationContext(
        repository=getenv("GITHUB_REPOSITORY_NAME", getenv("GITHUB_REPOSITORY", "unknown")),
        workflow=getenv("GITHUB_WORKFLOW_NAME", getenv("GITHUB_WORKFLOW", "unknown")),
        run_id=getenv("GITHUB_RUN_ID", "unknown"),
        run_attempt=getenv("GITHUB_RUN_ATTEMPT", "unknown"),
        run_url=getenv("GITHUB_RUN_URL"),
        ref_name=getenv("GITHUB_REF_NAME"),
        sha=getenv("GITHUB_SHA"),
        actor=getenv("GITHUB_ACTOR"),
        event_name=getenv("GITHUB_EVENT_NAME"),
        test_result=getenv("PYTHON_UNIT_TEST_RESULT", "unknown"),
        notification_test=truthy(getenv("NOTIFICATION_TEST")),
        dry_run=truthy(getenv("NOTIFICATION_DRY_RUN")),
    )


def main() -> int:
    ctx = build_context()
    print(f"Notification mode: {ctx.mode}")
    print(f"Python unit test result: {ctx.test_result}")

    if not ctx.should_notify:
        print("Notifications skipped because tests did not fail and no manual notification mode was requested.")
        return 0

    providers = [
        notify_slack,
        notify_discord,
        notify_teams,
        notify_mailgun,
        notify_twilio,
    ]

    failures = 0
    for provider in providers:
        try:
            provider(ctx)
        except NotificationError as exc:
            failures += 1
            print(f"{provider.__name__}: failed: {exc}", file=sys.stderr)

    if failures:
        print(f"Notification providers completed with {failures} failure(s).", file=sys.stderr)
        return 1

    print("Notification providers completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
