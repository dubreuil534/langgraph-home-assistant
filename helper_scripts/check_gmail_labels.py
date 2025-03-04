#!/usr/bin/env python3
import os
import sys
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add the parent directory to the Python module search path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.google_auth import load_auth_client  # Now Python should locate the module

def ensure_custom_labels_exist() -> dict:
    """
    Ensures that a set of custom labels exist in Gmail. If a label does not exist,
    it is created. Returns a mapping of label names to their Gmail label IDs.
    """
    # List of desired custom labels that you have added to your gmail account
    custom_labels = [
        "web3_newsletter",
        "marketing",
        "work",
        "personal",
        "action_required",
        "potential_delete"
    ]
    
    try:
        creds = load_auth_client()
        service = build("gmail", "v1", credentials=creds)
        
        # Get existing labels
        existing = service.users().labels().list(userId="me").execute().get("labels", [])
        label_mapping = {label["name"]: label["id"] for label in existing}
        
        # Create any missing labels
        for label in custom_labels:
            if label not in label_mapping:
                new_label = service.users().labels().create(
                    userId="me",
                    body={
                        "name": label,
                        "labelListVisibility": "labelShow",
                        "messageListVisibility": "show"
                    }
                ).execute()
                label_mapping[label] = new_label["id"]
                print(f"Created label '{label}' with id: {new_label['id']}")
            else:
                print(f"Label '{label}' already exists with id: {label_mapping[label]}")
        
        return label_mapping
    except HttpError as error:
        print(f"An error occurred: {error}")
        return {"error": str(error)}

if __name__ == "__main__":
    labels = ensure_custom_labels_exist()
    # Save the label mapping to a file for later use
    output_file = "gmail_labels.json"
    with open(output_file, "w") as f:
        json.dump(labels, f, indent=2)
    print(f"Label mapping saved to {output_file}")