import logging
from typing import Any, Dict, List

from utils.helpers import (
    process_config_file,
    send_completion_notifications,
)

from utils.github.client import (
    GitHubAPIClient,
)

logger = logging.getLogger(__name__)

def process_org_repos(organisation: str, api_token: str, conf_options: Dict[str, Any]) -> None:
    client = GitHubAPIClient(
        api_token,
        conf_options["APP"]["GITHUB_API_BASE_URL"],
    )

    # Fetch organization-specific webhooks if provided, else just use the global ones
    org_conf = next((org for org in conf_options["APP"]["ORGANISATIONS"] if org["name"] == organisation), {})
    org_specific_webhooks: List[Dict[str, Any]] = org_conf.get("webhooks_to_add", [])
    
    # Combine global webhooks with organization-specific webhooks
    webhooks_to_add: List[Dict[str, Any]] = conf_options["APP"]["WEBHOOKS_URLS_TO_ADD"] + org_specific_webhooks

    repos = client.get_org_repos(organisation)

    for repo in repos:
        webhooks = client.list_webhooks(organisation, repo["name"])
        logger.debug(f"Webhooks for {organisation}/{repo['name']}: {webhooks}")

        for webhook_data in webhooks_to_add:
            webhook_url = webhook_data["url"]
            events = webhook_data["events"]

            if not any(
                webhook["config"]["url"] == webhook_url for webhook in webhooks
            ):
                client.create_webhook(organisation, repo["name"], webhook_url, events)
                logger.info(f"Webhook added to {organisation}/{repo['name']}")
            else:
                # Delete any webhooks that are not in the list of webhooks to add.
                for webhook in webhooks:
                    if webhook["config"]["url"] not in [w["url"] for w in webhooks_to_add]:
                        logger.info(f"Webhook URL: {webhook['config']['url']}")

                        client.delete_webhook(organisation, repo["name"], webhook["id"])
                        logger.info(f"Webhook deleted from {organisation}/{repo['name']}")
                    else:
                        logger.info(f"Webhook already exists in {organisation}/{repo['name']}")

def process_user_repos(user: str, api_token: str, conf_options: Dict[str, Any]) -> None:
    client = GitHubAPIClient(
        api_token,
        conf_options["APP"]["GITHUB_API_BASE_URL"],
    )

    webhooks_to_add: List[Dict[str, Any]] = conf_options["APP"]["WEBHOOKS_URLS_TO_ADD"]

    repos = client.get_user_repos(user)

    for repo in repos:
        webhooks = client.list_webhooks(user, repo["name"])
        logger.debug(f"Webhooks for {user}/{repo['name']}: {webhooks}")

        for webhook_data in webhooks_to_add:
            webhook_url = webhook_data["url"]
            events = webhook_data["events"]

            if not any(
                webhook["config"]["url"] == webhook_url for webhook in webhooks
            ):
                client.create_webhook(user, repo["name"], webhook_url, events)
                logger.info(f"Webhook added to {user}/{repo['name']}")
            else:
                # Delete any webhooks that are not in the list of webhooks to add.
                for webhook in webhooks:
                    if webhook["config"]["url"] not in [w["url"] for w in webhooks_to_add]:
                        logger.info(f"Webhook URL: {webhook['config']['url']}")

                        client.delete_webhook(user, repo["name"], webhook["id"])
                        logger.info(f"Webhook deleted from {user}/{repo['name']}")
                    else:
                        logger.info(f"Webhook already exists in {user}/{repo['name']}")

def main() -> None:
    conf_options = process_config_file()

    if conf_options["APP"]["DEBUG"]:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    for organisation in conf_options["APP"]["ORGANISATIONS"]:
        process_org_repos(organisation["name"], organisation["token"], conf_options)

        logger.info(f"Succesfully processed organisation: {organisation['name']}")
    
    for user in conf_options["APP"]["USERS"]:
        process_user_repos(user["name"], user["token"], conf_options)

        logger.info(f"Succesfully processed user: {user['name']}")

    send_completion_notifications(conf_options)

    logger.info("Script completed successfully")


if __name__ == "__main__":
    main()