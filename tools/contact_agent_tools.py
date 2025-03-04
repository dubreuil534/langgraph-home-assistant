import os
import json
from googleapiclient.discovery import build
from dotenv import load_dotenv
from langchain_core.tools import tool
from utils.google_auth import load_auth_client

load_dotenv()

CONTACT_GOOGLE_SHEET = os.getenv("CONTACT_GOOGLE_SHEET")

@tool
def get_contacts():
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
    READ_RANGE = "contacts!A1:B3"

    result = sheet.values().get(
        spreadsheetId=CONTACT_GOOGLE_SHEET,
        range=READ_RANGE
    ).execute()
    
    rows = result.get("values", [])

    return {"data": rows}

@tool
def get_single_contact(query: str):
    """
    Retrieves a specific contact by name or email from Google Sheets using user OAuth.
    
    Parameters:
        query (str): The name or email to search for.
        
    Returns:
        dict: The contact details if found or an informative message.
    """
    # 1) Obtain valid credentials
    creds = load_auth_client()

    # 2) Build the Sheets API client
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()

    # 3) Read the full range of contacts.
    # Adjust the range if you have more rows. Here we assume the data starts at A1.
    READ_RANGE = "contacts!A1:B"
    result = sheet.values().get(
        spreadsheetId=CONTACT_GOOGLE_SHEET,
        range=READ_RANGE
    ).execute()
    rows = result.get("values", [])
    
    if not rows:
        return {"data": "No contacts found."}
    
    found_contact = None
    # Optionally, if your sheet has a header row, skip it.
    for i, row in enumerate(rows):
        # Skip header row if detected (assuming header contains "name" and "email")
        if i == 0 and len(row) >= 2 and row[0].strip().lower() == "name" and row[1].strip().lower() == "email":
            continue
        
        # Extract name and email from the row; handle missing values gracefully.
        name = row[0] if len(row) > 0 else ""
        email = row[1] if len(row) > 1 else ""
        
        # Case-insensitive search in both name and email
        if query.lower() in name.lower() or query.lower() in email.lower():
            found_contact = {"name": name, "email": email}
            break

    if found_contact:
        return {"data": found_contact}
    else:
        return {"data": f"No contact found matching '{query}'."}