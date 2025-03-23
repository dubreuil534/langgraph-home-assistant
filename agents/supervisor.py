from typing import Literal
from typing_extensions import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from config import load_yaml_config
from agents_config import members

config = load_yaml_config()

agent_members_prompt = []

for agent_key, agent_data in config["agents"].items():
    if not agent_data['name'] in members:
        continue
    # Create the header line with agent name and description
    header = f"{agent_data['name']}: {agent_data['description']}"
    agent_members_prompt.append(header)
    
    # Append each tool in the agent's tools list
    for tool in agent_data.get("tools", []):
        agent_members_prompt.append(f"- {tool}")
    
    # Add a blank line to separate agents
    agent_members_prompt.append("")

# Join all lines into a single string
agent_members_prompt_final = "\n".join(agent_members_prompt)

# # Create LLM instance (or import from shared config)
supervisor_llm = ChatOllama(model ="deepseek-r1:7b")

class State(MessagesState):
    next: str

# Define the supervisor output schema
class SupervisorOutput(TypedDict):
    next: Literal[*members, "FINISH"]
    task_description_for_agent: str
    message_completion_summary: str

# The main supervisor system prompt
supervisor_system_prompt = f"""
# Role
You are Anna's personal assistant supervisor Agent. Your job is to ensure that tasks related to his calendar, Notion lists, meal planning, and development are executed efficiently by your subagents.
# Context
You have access to the following {len(members)} subagents: {members}. Each subagent has its own specialized prompt and set of tools. Here is a description:
{agent_members_prompt_final}
# Objective
Analyze the user's request, decompose it into sub-tasks, and delegate each sub-task to the most appropriate subagent and ensure the task is completed.
# Instructions
1. Understand the user's goal.
2. Decompose the task into ordered sub-tasks.
3. For each sub-task, determine the best-suited agent.
4. When delegating, generate a tailored instruction message for the selected agent that:  
   - Specifies the task clearly based on the user’s request.  
   - Includes all necessary details like meal planning with date, and calendar entries with dish name and ingredients.  
   - Focuses on the outputs without mentioning other agents' functions or next steps. 
5. When receiving messages from the agents assess them thoroughly for completion
6. When all work is done, respond with next = FINISH.
# Helpful Information
- When asked for meal plans - only create dinner plans.
- When asked sending an email you may need to consult the contact_agent to accquire the correct email address
# Important
Delegating tasks should be added to the task_description_for_agent feild
Assess each message from sub agents carefully and decide whether the task is complete or not
# Examples
When delegating a list of meals to be added to the calendar it should look like this:
### Dinner Meal Plan\n\n**February 26 (Monday)**: \n- **Bonus veggie stew**  \n  - Ingredients: Carrots, potatoes, celery, onion, garlic, canned tomatoes, kidney beans, chickpeas, vegetable stock, bay leaves, thyme, olive oil\n\n**February 27 (Tuesday)**: \n- **Kikärtsgyros**  \n  - Ingredients: Chickpeas, red onion, garlic, cumin, smoked paprika, yogurt, cucumber, tomato, pita bread\n\n**February 28 (Wednesday)**: \n- **Italian bean soup**  \n  - Ingredients: White beans, canned tomatoes, onion, garlic, carrot, celery, vegetable stock, rosemary, Parmesan cheese\n,please add these to the family calendar.
"""

def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
    # Combine the supervisor system prompt with the conversation history.
    messages = [{"role": "system", "content": supervisor_system_prompt}] + state["messages"]
    response = supervisor_llm.with_structured_output(SupervisorOutput).invoke(messages)
    goto = response["next"]

    if goto == "FINISH":
        return Command(goto=END, update={"next": END})

    # Append the tailored instructions to the conversation history.
    new_messages = [{"role": "system", "content": response["task_description_for_agent"]}]
    return Command(goto=goto, update={"next": goto, "messages": new_messages})