# tools/calendar.py
import os
from datetime import datetime, timezone
import pytz
from dotenv import load_dotenv
from langchain_core.tools import tool
from typing import Any
from googleapiclient.discovery import build
from utils.google_auth import load_auth_client

load_dotenv()

FAMILY_CAL = os.getenv("FAMILY_CAL")
PERSONAL_CAL = os.getenv("PERSONAL_CAL")
WORK_CAL = os.getenv("WORK_CAL")

CALENDAR_IDS = {
  "family": FAMILY_CAL,
  "personal": PERSONAL_CAL,
  "work": WORK_CAL
}

@tool
def get_current_date_and_time() -> Any:
    """Get the current date and time."""
    stockholm_tz = pytz.timezone('Europe/Stockholm')
    now = datetime.now(stockholm_tz)
    return {
        "datetime": now.strftime('%Y-%m-%d %H:%M:%S'),
        "day_of_the_week": now.strftime("%A")
    }

def parse_event(event: dict, calendar_id: str) -> dict:
    """
    Parse an individual event from the Google Calendar API response.
    
    Args:
        event (dict): The raw event dictionary from the API.
        calendar_id (str): The calendar ID this event belongs to.
    
    Returns:
        dict: A simplified dictionary containing key event information.
    """
    return {
        'calendarId': calendar_id,
        'status': event.get('status'),
        'summary': event.get('summary'),
        'start': event.get('start'),
        'end': event.get('end'),
        'description': event.get('description', None)
    }

def get_event_start(event: dict) -> datetime:
    """
    Extract and convert the event's start time into a timezone-aware datetime object for sorting.
    
    It checks for 'dateTime' first, and falls back to 'date'. For date-only values, the Europe/Stockholm
    timezone is attached.
    
    Args:
        event (dict): The parsed event dictionary.
    
    Returns:
        datetime: A timezone-aware datetime object representing the event's start time.
    """
    start_info = event.get('start', {})
    
    if 'dateTime' in start_info:
        start_str = start_info.get('dateTime')
        # Replace trailing 'Z' with '+00:00' for compatibility.
        if start_str.endswith('Z'):
            start_str = start_str[:-1] + '+00:00'
        try:
            dt = datetime.fromisoformat(start_str)
            return dt
        except Exception as e:
            return datetime(1970, 1, 1, tzinfo=timezone.utc)
    elif 'date' in start_info:
        start_str = start_info.get('date')
        try:
            # Parse date-only string (e.g. "2025-02-14") and attach the Europe/Stockholm timezone.
            dt = datetime.fromisoformat(start_str)
            dt = dt.replace(tzinfo=ZoneInfo("Europe/Stockholm"))
            return dt
        except Exception as e:
            return datetime(1970, 1, 1, tzinfo=timezone.utc)
    else:
        # Fallback value if no valid start is found.
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def format_datetime(dt: datetime) -> str:
    """
    Format a timezone-aware datetime object into an RFC3339-compliant string.
    
    Args:
        dt (datetime): A timezone-aware datetime object.
        
    Returns:
        str: ISO formatted string with 'Z' for UTC.
    """
    # Ensure the datetime is timezone-aware. If not, assume UTC.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Convert to ISO format and replace '+00:00' with 'Z'
    return dt.isoformat().replace("+00:00", "Z")

@tool
def get_calendar_events(start_date: str = None, end_date: str = None) -> list:
    """
    Fetch events from multiple calendars between a start and end date.

    Args:
        start_date (str, optional): The earliest date/time (ISO string) for events.
        end_date (str, optional): The latest date/time (ISO string) for events.

    Returns:
        list: A list of parsed event dictionaries.
    """
    try:
        # Load authorized credentials and build the Calendar service.
        creds = load_auth_client()
        service = build('calendar', 'v3', credentials=creds)

        # Prepare timeMin and timeMax in RFC3339 format (UTC).
        if start_date:
            dt_start = datetime.fromisoformat(start_date)
            time_min = format_datetime(dt_start)
        else:
            time_min = format_datetime(datetime.now(timezone.utc))

        time_max = None
        if end_date:
            dt_end = datetime.fromisoformat(end_date)
            time_max = format_datetime(dt_end)

        all_events = []

        # Loop through each calendar defined in CALENDAR_IDS.
        for calendar_name, calendar_id in CALENDAR_IDS.items():
            response = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                timeZone='Europe/Stockholm',
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            items = response.get('items', [])
            # Parse each event into a simplified dictionary.
            events = [parse_event(event, calendar_id) for event in items]

            all_events.extend(events)

        # Sort all events by their start time.
        all_events.sort(key=get_event_start)
        return all_events

    except Exception as error:
        print(error)
        raise Exception("Failed to retrieve events.") from error

@tool
def add_calendar_event(startDate: datetime, endDate: datetime, calendar_name: str, title: str, description: str) -> dict:
    """
    Adds a new event to a Google Calendar.

    Args:
        startDate (datetime): The start date and time of the event.
        endDate (datetime): The end date and time of the event.
        calendar_name (str): The name of the calendar where the event will be added.
        title (str): The title of the event.
        description (str): The description of the event.

    Returns:
        dict: The newly created event as returned by the Google Calendar API.
    """
    if calendar_name not in CALENDAR_IDS:
        raise ValueError(f"Calendar name '{calendar_name}' not found in the calendar mapping.")
    calendar_id = CALENDAR_IDS[calendar_name]

    event = {
        "summary": title,
        "description": description,
        "calendarId":calendar_id,
        "start": {
            "dateTime": startDate.isoformat(),
            "timeZone": "Europe/Stockholm"
        },
        "end": {
            "dateTime": endDate.isoformat(),
            "timeZone": "Europe/Stockholm"
        }
    }

    creds = load_auth_client()
    service = build('calendar', 'v3', credentials=creds)

    try:
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()
        return created_event
    except Exception as e:
        print("Error creating event:", e)
        raise