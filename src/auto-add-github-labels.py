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

def delete_extra_labels(repo_name: str, current_labels: List[Dict[str, str]], labels_to_sync: List[Dict[str, str]], client: GitHubAPIClient, owner: str) -> None:
    config_label_names = {label['name'] for label in labels_to_sync}

    # Delete labels that are not in the configuration
    for label in current_labels:
        if label['name'] not in config_label_names:
            client.delete_label(owner, repo_name, label['name'])
            logger.info(f"Deleted label {label['name']} from {repo_name}")

def add_missing_labels(repo_name: str, current_labels: List[Dict[str, str]], labels_to_sync: List[Dict[str, str]], client: GitHubAPIClient, owner: str) -> None:
    current_label_names = {label['name'] for label in current_labels}

    # Add missing labels that are in the config but not in the repository
    for label in labels_to_sync:
        if label['name'] not in current_label_names:
            client.create_label(owner, repo_name, label['name'], label['color'], label['description'])
            logger.info(f"Added label {label['name']} to {repo_name}")

def process_repo_labels(owner: str, repo_name: str, labels_to_sync: List[Dict[str, str]], client: GitHubAPIClient) -> None:
    # Get current labels from the repository
    current_labels = client.list_labels(owner, repo_name)

    # First, delete labels that are not in the configuration
    delete_extra_labels(repo_name, current_labels, labels_to_sync, client, owner)

    # Then, add missing labels that are in the configuration but not in the repo
    add_missing_labels(repo_name, current_labels, labels_to_sync, client, owner)

def process_org_repos(organisation: str, api_token: str, conf_options: Dict[str, Any]) -> None:
    client = GitHubAPIClient(
        api_token,
        conf_options["APP"]["GITHUB_API_BASE_URL"],
    )

    repos = client.get_org_repos(organisation)

    for repo in repos:
        repo_name = repo['name']
        # Get standard labels from the config
        standard_labels = conf_options["APP"]["ORGANISATIONS"][0]["standard_labels"]

        # Check if the repository is in the config for specific backend/frontend label management
        for conf_repo in conf_options["APP"]["ORGANISATIONS"][0]["repositories"]:
            if conf_repo['name'] == repo_name:
                # If repo is found in config, combine standard labels with backend/frontend labels
                if conf_repo['type'] == "backend":
                    additional_labels = conf_options["APP"]["ORGANISATIONS"][0]["backend_labels"]
                elif conf_repo['type'] == "frontend":
                    additional_labels = conf_options["APP"]["ORGANISATIONS"][0]["frontend_labels"]
                else:
                    logger.error(f"Unknown repo type: {conf_repo['type']} for {repo_name}")
                    break

                labels_to_sync = standard_labels + additional_labels
                process_repo_labels(organisation, repo_name, labels_to_sync, client)
                logger.info(f"Processed labels for {repo_name} ({conf_repo['type']})")
                break
        else:
            # If the repo is not found in the config, only apply the standard labels
            process_repo_labels(organisation, repo_name, standard_labels, client)
            logger.info(f"Processed standard labels for {repo_name} (not in config)")

def process_user_repos(user: str, api_token: str, conf_options: Dict[str, Any]) -> None:
    client = GitHubAPIClient(
        api_token,
        conf_options["APP"]["GITHUB_API_BASE_URL"],
    )

    repos = client.get_user_repos(user)

    for repo in repos:
        repo_name = repo['name']
        # Get standard labels from the config
        standard_labels = conf_options["APP"]["ORGANISATIONS"][0]["standard_labels"]

        # Check if the user repo is in the config for specific backend/frontend label management
        for conf_repo in conf_options["APP"]["USERS"]:
            if conf_repo['name'] == user:
                # Apply additional logic for user repos if needed (e.g., frontend/backend)
                repo_type = "frontend"  # or "backend", adjust logic if needed
                labels_to_sync = standard_labels  # Add more logic for specific labels if needed

                process_repo_labels(user, repo_name, labels_to_sync, client)
                logger.info(f"Processed labels for {repo_name} (User: {user}, Type: {repo_type})")
                break
        else:
            # If the repo is not found in the config, only apply the standard labels
            process_repo_labels(user, repo_name, standard_labels, client)
            logger.info(f"Processed standard labels for {repo_name} (User: {user}, not in config)")

def main() -> None:
    conf_options = process_config_file()

    if conf_options["APP"]["DEBUG"]:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    for organisation in conf_options["APP"]["ORGANISATIONS"]:
        process_org_repos(organisation["name"], organisation["token"], conf_options)
        logger.info(f"Successfully processed organisation: {organisation['name']}")

    for user in conf_options["APP"]["USERS"]:
        if user["token"]:  # Check if the user has a token
            process_user_repos(user["name"], user["token"], conf_options)
            logger.info(f"Successfully processed user repositories: {user['name']}")

    send_completion_notifications(conf_options)

    logger.info("Script completed successfully")


if __name__ == "__main__":
    main()
