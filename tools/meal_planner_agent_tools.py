import os
import json
from googleapiclient.discovery import build
from dotenv import load_dotenv
from langchain_core.tools import tool
from utils.google_auth import load_auth_client
from langgraph.types import interrupt

load_dotenv()

@tool
def get_recipes():
    """
    Fetches recipes from Google Sheets using user OAuth (NOT a service account).
    """
    # 1) Check if we already have a valid token stored in token.json
    # Use from_authorized_user_info() because combined_info is a dictionary.
    creds = load_auth_client()

    # 4) Build the Sheets API client with our valid creds
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()

    # 5) Read data from the sheet
    #    "RECIPES_GOOGLE_SHEET" is your sheet ID from .env
    READ_RANGE = "recipes_db!A1:B30"

    result = sheet.values().get(
        spreadsheetId=RECIPES_GOOGLE_SHEET,
        range=READ_RANGE
    ).execute()
    
    rows = result.get("values", [])
    print(rows)

    return {"data": rows}

@tool
def human_feedback(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query})
    return human_response["data"]