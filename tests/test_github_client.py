import pytest
import logging
from src.github_client import get_pull_request_data
from src.model import query_openai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# This test should be run sparingly due to its impact on API rate limits and potential costs.

@pytest.mark.integration
def test_integration_with_real_endpoints():
    repo_name = "octocat/Hello-World"
    pull_number = 6 

    # Fetch pull request data and diff from GitHub
    pr = get_pull_request_data(repo_name, pull_number)
    assert pr is not None, "Failed to fetch PR data"

    # Construct the prompt for OpenAI based on the fetched data
    prompt = f"Please review the following pull request:\nTitle: {pr.title}\nDescription: {pr.description}\nDiff: {pr.diff}\n"
    logging.info(f"Sending the following prompt to OpenAI: {prompt}")

    # Send the prompt to OpenAI and get a response
    response = query_openai(prompt)
    logging.info(f"Received the following response from OpenAI: {response}")

    assert response is not None and response != "", "No response received from OpenAI"