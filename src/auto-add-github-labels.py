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

def sync_labels(repo_name: str, labels_to_sync: List[Dict[str, str]], current_labels: List[Dict[str, str]], client: GitHubAPIClient, owner: str) -> None:
    current_label_names = {label['name'] for label in current_labels}
    config_label_names = {label['name'] for label in labels_to_sync}

    # Add missing labels
    for label in labels_to_sync:
        if label['name'] not in current_label_names:
            client.create_label(owner, repo_name, label['name'], label['color'], label['description'])
            logger.info(f"Added label {label['name']} to {repo_name}")

    # Delete extra labels
    for label in current_labels:
        if label['name'] not in config_label_names:
            client.delete_label(owner, repo_name, label['name'])
            logger.info(f"Deleted label {label['name']} from {repo_name}")

def process_repo_labels(owner: str, repo_name: str, repo_type: str, client: GitHubAPIClient, conf_options: Dict[str, Any]) -> None:
    # Get standard labels from the config
    standard_labels = conf_options["APP"]["ORGANISATIONS"][0]["standard_labels"]
    
    # Determine which additional labels to use (backend or frontend)
    if repo_type == "backend":
        additional_labels = conf_options["APP"]["ORGANISATIONS"][0]["backend_labels"]
    elif repo_type == "frontend":
        additional_labels = conf_options["APP"]["ORGANISATIONS"][0]["frontend_labels"]
    else:
        logger.error(f"Unknown repo type: {repo_type} for {repo_name}")
        return

    # Combine standard labels with backend/frontend labels
    labels_to_sync = standard_labels + additional_labels

    # Get current labels from the repository
    current_labels = client.list_labels(owner, repo_name)

    # Sync labels (add missing, delete extra)
    sync_labels(repo_name, labels_to_sync, current_labels, client, owner)

def process_org_repos(organisation: str, api_token: str, conf_options: Dict[str, Any]) -> None:
    client = GitHubAPIClient(
        api_token,
        conf_options["APP"]["GITHUB_API_BASE_URL"],
    )

    repos = client.get_org_repos(organisation)

    for repo in repos:
        repo_name = repo['name']
        # Identify if the repository is frontend or backend
        for conf_repo in conf_options["APP"]["ORGANISATIONS"][0]["repositories"]:
            if conf_repo['name'] == repo_name:
                process_repo_labels(organisation, repo_name, conf_repo['type'], client, conf_options)
                logger.info(f"Processed labels for {repo_name} ({conf_repo['type']})")
                break
        else:
            logger.warning(f"Repository {repo_name} not configured for label management.")

def process_user_repos(user: str, api_token: str, conf_options: Dict[str, Any]) -> None:
    client = GitHubAPIClient(
        api_token,
        conf_options["APP"]["GITHUB_API_BASE_URL"],
    )

    repos = client.get_user_repos(user)

    for repo in repos:
        repo_name = repo['name']
        # Assuming user repositories follow the same config structure for frontend/backend types
        # Add logic to determine repo type for user repos
        for conf_repo in conf_options["APP"]["USERS"]:
            if conf_repo['name'] == user:
                # Assume a common type for all user repos, or add specific logic to define repo types here
                repo_type = "frontend"  # or "backend" or define based on your needs
                process_repo_labels(user, repo_name, repo_type, client, conf_options)
                logger.info(f"Processed labels for {repo_name} (User: {user}, Type: {repo_type})")
                break
        else:
            logger.warning(f"Repository {repo_name} not configured for label management.")

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
