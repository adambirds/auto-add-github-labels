import json
from datetime import datetime, timezone
from typing import Any, Dict

import requests


def send_completion_discord_message(config_options: Dict[str, Any]) -> None:
    headers = {"Content-Type": "application/json"}

    with open("templates/discord/script-complete.json", "r") as f:
        payload = json.load(f)

    payload["embeds"][0]["timestamp"] = datetime.now(tz=timezone.utc).isoformat()

    payload = json.dumps(payload, indent=4)

    requests.request(
        "POST", config_options["APP"]["DISCORD_WEBHOOK_COMPLETION"], headers=headers, data=payload
    )


def send_error_discord_message(error: str, config_options: Dict[str, Any]) -> None:
    headers = {"Content-Type": "application/json"}

    with open("templates/discord/script-error.json", "r") as f:
        payload = json.load(f)

    payload["embeds"][0]["fields"][0]["value"] = error
    payload["embeds"][0]["timestamp"] = datetime.now(tz=timezone.utc).isoformat()

    payload = json.dumps(payload, indent=4)

    requests.request(
        "POST", config_options["APP"]["DISCORD_WEBHOOK_ERROR"], headers=headers, data=payload
    )