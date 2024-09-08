from typing import Any, Dict

import yaml

from utils.notifications.discord import (
    send_completion_discord_message,
    send_error_discord_message,
)
from utils.notifications.slack import (
    send_completion_slack_message,
    send_error_slack_message,
)
from utils.notifications.teams import (
    send_completion_teams_message,
    send_error_teams_message,
)

from utils.notifications.zabbix import (
    send_zabbix_script_monitoring,
)


def process_config_file() -> Dict[str, Any]:

    with open("config.yaml", "r") as stream:
        config_options = yaml.safe_load(stream)

    return config_options


def send_error_notifications(error: str, conf_options: Dict[str, Any]) -> None:
    if "Discord" in conf_options["APP"]["NOTIFICATIONS"]:
        send_error_discord_message(
            error,
            conf_options,
        )
    if "Slack" in conf_options["APP"]["NOTIFICATIONS"]:
        send_error_slack_message(
            error,
            conf_options,
        )
    if "Teams" in conf_options["APP"]["NOTIFICATIONS"]:
        send_error_teams_message(
            error,
            conf_options,
        )


def send_completion_notifications(conf_options: Dict[str, Any]) -> None:
    if "Discord" in conf_options["APP"]["NOTIFICATIONS"]:
        send_completion_discord_message(conf_options)
    if "Slack" in conf_options["APP"]["NOTIFICATIONS"]:
        send_completion_slack_message(conf_options)
    if "Teams" in conf_options["APP"]["NOTIFICATIONS"]:
        send_completion_teams_message(conf_options)
    if "Zabbix" in conf_options["APP"]["SCRIPT_MONITORING"]:
        send_zabbix_script_monitoring(0, conf_options)