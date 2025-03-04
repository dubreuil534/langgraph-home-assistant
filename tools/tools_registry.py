from tools.meal_planner_agent_tools import get_recipes, human_feedback
from tools.calendar_agent_tools import get_current_date_and_time, get_calendar_events, add_calendar_event
from tools.notion_agent_tools import get_shopping_list, add_entry_to_mindbase, add_to_shopping_list
from tools.contact_agent_tools import get_contacts, get_single_contact
from tools.email_agent_tools import send_email, check_emails, label_email, create_draft

TOOLS_REGISTRY = {
  "get_recipes" : get_recipes,
  "get_current_date_and_time" : get_current_date_and_time,
  "get_calendar_events" : get_calendar_events,
  "add_calendar_event" : add_calendar_event,
  "get_shopping_list" : get_shopping_list,
  "add_entry_to_mindbase" : add_entry_to_mindbase,  
  "add_to_shopping_list" : add_to_shopping_list,
  "human_feedback": human_feedback,
  "get_contacts": get_contacts,
  "get_single_contact" : get_single_contact,
  "send_email": send_email,
  "check_emails": check_emails,
  "label_email": label_email,
  "create_draft": create_draft
}