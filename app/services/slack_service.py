"""Slack webhook integration — post meeting analysis as a formatted message."""
import os
import json
import logging
import requests

logger = logging.getLogger(__name__)


def post_meeting_to_slack(summary: str, action_items: list[dict], key_decisions: list[str]) -> None:
    """
    Formats and posts meeting analysis to the configured Slack Incoming Webhook URL.
    Raises RuntimeError if the webhook is not configured or the request fails.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        raise ValueError("SLACK_WEBHOOK_URL is not set in environment variables.")

    # Build message text
    lines = ["📌 *Meeting Summary*", summary, ""]

    lines.append("✅ *Action Items*")
    if action_items:
        for item in action_items:
            owner = item.get("owner", "Unassigned")
            task = item.get("task", "")
            deadline = item.get("deadline", "Not specified")
            priority = item.get("priority", "Medium")
            lines.append(f"• {owner} → {task} by {deadline} [{priority}]")
    else:
        lines.append("• None identified")

    lines.append("")
    lines.append("✔ *Key Decisions*")
    if key_decisions:
        for decision in key_decisions:
            lines.append(f"• {decision}")
    else:
        lines.append("• None identified")

    message = "\n".join(lines)

    response = requests.post(
        webhook_url,
        data=json.dumps({"text": message}),
        headers={"Content-Type": "application/json"},
        timeout=10,
    )

    if response.status_code != 200:
        logger.error("Slack webhook error %s: %s", response.status_code, response.text)
        raise RuntimeError(f"Slack webhook failed: {response.status_code} {response.text}")

    logger.info("Meeting analysis posted to Slack successfully")
