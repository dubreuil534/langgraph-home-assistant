import os
import requests
from dotenv import load_dotenv
from typing import Any, List
from langchain_core.tools import tool

load_dotenv()

# Retrieve other API keys/URLs
SHOPPING_PAGE_ID = os.getenv("SHOPPING_PAGE_ID")
MIND_BASE_DB_ID = os.getenv("MIND_BASE_DB_ID")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_API_URL_PAGES = 'https://api.notion.com/v1/pages'
NOTION_API_URL_BLOCKS = 'https://api.notion.com/v1/blocks'

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"  # Use the appropriate Notion API version
}

@tool
def get_shopping_list() -> Any:
    """
    Fetches all unchecked shopping list items from the shopping list.
    """
    try:
        # Construct the URL for retrieving children blocks of the page
        url = f"{NOTION_API_URL_BLOCKS}/{SHOPPING_PAGE_ID}/children?page_size=100"

        # Fetch the blocks from the page
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        data = response.json()
        blocks = data.get("results", [])

        # Filter for 'to_do' blocks that are unchecked, then extract their text content
        unchecked_items = []
        for block in blocks:
            if block.get("type") == "to_do":
                to_do = block.get("to_do", {})
                if to_do.get("checked") is False:
                    rich_text_list = to_do.get("rich_text", [])
                    text_content = ''.join(rt.get("plain_text", "") for rt in rich_text_list)
                    unchecked_items.append(text_content)

        return unchecked_items
    except requests.exceptions.RequestException as error:
        status = error.response.status_code if error.response else "No Status"
        try:
            error_data = error.response.json() if error.response else str(error)
        except ValueError:
            error_data = str(error)
        print(f"Failed to fetch unchecked  items from Notion: {status} {error_data}")
        raise Exception(error_data)

@tool
def add_entry_to_mindbase(entryContent: str, entryType: str) -> Any:
    """
    Adds a new entry to the Mind Base database with a 'Name' and 'Type' property.
    """
    try:
        data = {
            "parent": { "database_id": MIND_BASE_DB_ID },
            "properties": {
                "Name": {
                    "title": [
                        {
                            "type": "text",
                            "text": { "content": entryContent },
                        },
                    ],
                },
                "Type": {
                    "select": {
                        "name": entryType,
                    },
                },
            },
        }
        response = requests.post(NOTION_API_URL_PAGES, json=data, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as error:
        status = error.response.status_code if error.response else "No Status"
        try:
            error_data = error.response.json() if error.response else str(error)
        except ValueError:
            error_data = str(error)
        print(f"Failed to add entry to Notion: {status} {error_data}")
        raise Exception(error_data)

@tool
def add_to_shopping_list(data: List[str]) -> Any:
    """
    Adds multiple shopping items to the shopping list.
    """
    try:
        url = f"{NOTION_API_URL_BLOCKS}/{SHOPPING_PAGE_ID}/children"
        data = {
            "children": [
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": item,
                                }
                            }
                        ],
                        "checked": False,
                    },
                }
                for item in data
            ]
        }
        response = requests.patch(url, json=data, headers=headers)
        response.raise_for_status()  # Raises an HTTPError if the response was an error
        return response.json()
    except requests.exceptions.RequestException as error:
        status = error.response.status_code if error.response else "No Status"
        try:
            error_data = error.response.json() if error.response else str(error)
        except ValueError:
            error_data = str(error)
        print(f"Failed to add to-dos to Notion page: {status} {error_data}")
        raise Exception(error_data)