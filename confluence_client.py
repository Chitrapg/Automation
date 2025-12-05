from datetime import datetime
from typing import Dict, Any, Optional

import requests

from config import (
    CONFLUENCE_USERNAME,
    CONFLUENCE_API_TOKEN,
    CONFLUENCE_BASE_URL,
    CONFLUENCE_SPACE_KEY,
    PARENT_PAGE_ID,
    validate_confluence_config,
)


def create_confluence_page(title: str, html_content: str) -> Dict[str, Any]:
    """
    Create a Confluence page using the REST API.

    :param title: Base title of the page (timestamp will be appended).
    :param html_content: HTML content to store in the page body.
    :return: Parsed JSON response from Confluence.
    """
    validate_confluence_config()

    url = f"{CONFLUENCE_BASE_URL}/rest/api/content"

    # Add unique timestamp to title so each run creates a new page
    unique_title = f"{title} – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # Base payload
    payload: Dict[str, Any] = {
        "type": "page",
        "title": unique_title,
        "space": {"key": CONFLUENCE_SPACE_KEY},
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage",  # 'storage' == Confluence XHTML format
            }
        },
    }

    # Optionally set parent page
    if PARENT_PAGE_ID:
        payload["ancestors"] = [{"id": PARENT_PAGE_ID}]

    response = requests.post(
        url,
        json=payload,
        auth=(CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN),
        headers={"Content-Type": "application/json"},
        timeout=60,
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Error creating Confluence page: {e}")
        print(f"Response Body: {response.text}")
        raise

    data = response.json()

    page_id = data.get("id")
    links = data.get("_links", {})
    webui = links.get("webui", "")
    base = links.get("base", "")

    full_url = f"{base}{webui}" if base and webui else "N/A"

    print("✅ Confluence page created successfully!")
    print("Page ID:", page_id)
    print("URL    :", full_url)

    return data
