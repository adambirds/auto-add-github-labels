import requests
import logging

logger = logging.getLogger(__name__)

class GitHubAPIClient:
    def __init__(self, token: str, base_api_url: str) -> None:
        self.token = token
        self.base_api_url = base_api_url.rstrip("/")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Bearer {self.token}",
        }
    
    def execute_api_call(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> dict:
        url = f"{self.base_api_url}/{endpoint}"
        
        if method == "GET" and params:
            response = requests.get(url, headers=self.headers, params=params)
        elif data:
            response = requests.post(url, headers=self.headers, json=data)
        else:
            response = requests.request(method, url, headers=self.headers)
        
        if response.status_code in (200, 201):
            return response.json()
        elif response.status_code == 204:
            return {}
        else:
            raise Exception(f"Failed to execute API call: {response.text}")
    
    def fetch_all(self, method: str, endpoint: str, params: dict = None) -> list:
        items = []
        page = 1
        while True:
            if params:
                params.update({'page': page})
            else:
                params = {'page': page, 'per_page': 100}  # Default per_page set to 100
            
            response = self.execute_api_call(method, endpoint, params=params)
            items.extend(response)  # Assuming response is a list of items
            
            # Break if there are no more items in the response
            if not response or len(response) < params['per_page']:
                break
            page += 1
        
        return items
    
    def get_org_repos(self, organisation: str) -> dict:
        return self.fetch_all("GET", f"orgs/{organisation}/repos")
    
    def get_user_repos(self, user: str) -> dict:
        return self.fetch_all("GET", f"users/{user}/repos")
    
    def list_labels(self, owner: str, repo: str) -> dict:
        return self.fetch_all("GET", f"repos/{owner}/{repo}/labels")
    
    def create_label(self, owner: str, repo: str, name: str, color: str, description: str) -> dict:
        logger.info(f"Creating label {name} in {owner}/{repo}")

        data = {
            "name": name,
            "color": color,
            "description": description,
        }
        
        return self.execute_api_call("POST", f"repos/{owner}/{repo}/labels", data=data)
    
    def delete_label(self, owner: str, repo: str, label_name: str) -> dict:
        logger.info(f"Deleting label {label_name} in {owner}/{repo}")
        return self.execute_api_call("DELETE", f"repos/{owner}/{repo}/labels/{label_name}")