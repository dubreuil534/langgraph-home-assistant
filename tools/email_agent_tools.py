import os
import re
import json
import html
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from dotenv import load_dotenv
from langchain_core.tools import tool
from utils.google_auth import load_auth_client

load_dotenv()

# You need to use the checl_email_labels.py tool to generate these for your own inbox.
EMAIL_LABELS = {
  "IMPORTANT": "IMPORTANT",
  "SPAM": "SPAM",
  "marketing": "Label_23092374_example"
}

def create_message(sender: str, to: str, subject: str, message_text: str) -> dict:
    """
    Create a message for an email.
    
    Args:
        sender (str): The email address of the sender.
        to (str): The email address of the receiver.
        subject (str): The subject of the email.
        message_text (str): The body of the email.
    
    Returns:
        dict: A dictionary with a base64url encoded email message.
    """
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    # Attach the email body text
    msg = MIMEText(message_text, 'plain')
    message.attach(msg)
    
    # Encode the message as base64url
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

@tool
def send_email(to_email: str, subject: str, body: str) -> dict:
    """
    Sends an email using the Gmail API.
    
    Args:
        to_email (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Body text of the email.
    
    Returns:
        dict: API response data or error information.
    """
    try:
        creds = load_auth_client()
        service = build("gmail", "v1", credentials=creds)
        sender = "me"
        message = create_message(sender, to_email, subject, body)
        sent_message = service.users().messages().send(userId="me", body=message).execute()
        print("Message sent successfully. Message Id:", sent_message.get("id"))
        return sent_message
    except HttpError as error:
        print(f"An error occurred: {error}")
        return {"error": str(error)}

def clean_body(text: str) -> str:
    """
    Unescapes HTML entities, removes all HTML tags, and eliminates URL links from the text.
    
    Args:
        text (str): The raw email body text.
    
    Returns:
        str: The cleaned text with HTML and URLs removed.
    """
    # Unescape HTML entities (e.g., &amp; -> &)
    text = html.unescape(text)
    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove URLs (e.g., http:// or https:// links)
    text = re.sub(r'http[s]?://\S+', '', text)
    # Remove any extra whitespace
    return text.strip()

def get_message_body(payload: dict) -> str:
    """
    Extracts, decodes, and cleans the plain text body from the Gmail message payload.
    
    Args:
        payload (dict): The payload of the Gmail message.
    
    Returns:
        str: The decoded and cleaned email body.
    """
    # Check if the payload has a direct body with data
    body = payload.get("body", {})
    data = body.get("data")
    if data:
        decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        return clean_body(decoded)
    
    # If the message is multipart, search for a text/plain part
    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                return clean_body(decoded)
    
    # Fallback: decode the first part that contains data
    for part in parts:
        data = part.get("body", {}).get("data")
        if data:
            decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            return clean_body(decoded)
    
    return ""

@tool
def check_emails(query: str = "", max_results: int = 10, only_unlabeled: bool = False) -> dict:
    """
    Retrieves a list of emails matching the given query, including a fully cleaned email body.
    Optionally, only returns emails with no user-applied labels.
    
    Args:
        query (str): Gmail search query (e.g., "is:unread", "from:someone@example.com").
        max_results (int): Maximum number of emails to retrieve.
        only_unlabeled (bool): If True, only return emails with no user-applied labels.
    
    Returns:
        dict: A dictionary containing a list of emails with details including id, snippet, labelIds, and cleaned body.
    """
    try:
        # Append "has:nouserlabels" to the query if only_unlabeled is True
        if only_unlabeled:
            query = (query + " " if query else "") + "has:nouserlabels"
        
        creds = load_auth_client()
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        messages = results.get("messages", [])
        email_list = []
        
        for msg in messages:
            msg_detail = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            payload = msg_detail.get("payload", {})
            body_text = get_message_body(payload)
            email_list.append({
                "id": msg_detail.get("id"),
                "snippet": msg_detail.get("snippet", ""),
                "labelIds": msg_detail.get("labelIds", []),
                "body": body_text
            })
        return {"emails": email_list}
    except HttpError as error:
        print(f"An error occurred: {error}")
        return {"error": str(error)}
@tool
def label_email(message_id: str, label: str) -> dict:
    """
    Adds a label to an email message by looking up its ID from the EMAIL_LABELS dictionary.
    
    Args:
        message_id (str): The ID of the email message.
        label (str): The label name to add (must be a key in EMAIL_LABELS).
    
    Returns:
        dict: The modified email message details or error information.
    """
    try:
        # Retrieve the label ID using the provided label name
        label_id = EMAIL_LABELS.get(label)
        if not label_id:
            return {"error": f"Label '{label}' not found in EMAIL_LABELS."}
        
        creds = load_auth_client()
        service = build("gmail", "v1", credentials=creds)
        body = {"addLabelIds": [label_id]}
        modified_message = service.users().messages().modify(userId="me", id=message_id, body=body).execute()
        print(f"Label '{label}' (ID: {label_id}) added to message '{message_id}'.")
        return modified_message
    except HttpError as error:
        print(f"An error occurred: {error}")
        return {"error": str(error)}

@tool
def create_draft(to_email: str, subject: str, body: str) -> dict:
    """
    Creates and stores a draft email in Gmail.

    Args:
        to_email (str): Recipient email address.
        subject (str): Subject of the email.
        body (str): Body text of the email.

    Returns:
        dict: The created draft's details or error information.
    """
    try:
        creds = load_auth_client()
        service = build("gmail", "v1", credentials=creds)
        sender = "me"
        message = create_message(sender, to_email, subject, body)
        
        # Create a draft from the message and store it in drafts
        draft = service.users().drafts().create(userId="me", body={"message": message}).execute()
        print("Draft created successfully with id:", draft.get("id"))
        return draft
    except HttpError as error:
        print(f"An error occurred: {error}")
        return {"error": str(error)}