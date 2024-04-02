# api_client.py

import requests

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def get(self, endpoint, params=None):
        """
        Send a GET request to the specified endpoint.
        """
        response = requests.get(f"{self.base_url}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint, data=None):
        """
        Send a POST request to the specified endpoint.
        """
        response = requests.post(f"{self.base_url}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

# Example usage
if __name__ == "__main__":
    # Example: Using the APIClient to interact with a hypothetical external service
    client = APIClient("https://api.example.com")

    # GET request example
    data = client.get("data/1")
    print("GET request data:", data)

    # POST request example
    new_data = {"name": "New Item", "value": "123"}
    response = client.post("data", data=new_data)
    print("POST request response:", response)
