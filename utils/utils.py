from config import load_yaml_config
from tools.tools_registry import TOOLS_REGISTRY

def parse_tool_name(tool_string: str) -> str:
    """
    Extract the tool name from a string of the form:
    'read_file(file_path: str): Reads the file content...'

    The tool name is the substring before the first '('.
    """
    # Split by '(' and take the left side
    name_part = tool_string.split('(', 1)[0]
    tool_name = name_part.strip()
    return tool_name

def get_agent_config(agent_name: str) -> dict:
    """
    Retrieves and formats the configuration for a specified agent.

    """
    config_data = load_yaml_config()

    all_agents = [
        {"name": agent, "description": details.get("description", "No description available")}
        for agent, details in config_data["agents"].items()
    ]

    if agent_name not in config_data["agents"]:
        raise KeyError(f"Agent '{agent_name}' not found in configuration.")

    agent_cfg = config_data["agents"][agent_name]
    agent_model = agent_cfg["model"]
    agent_tools = agent_cfg["tools"]
    tool_functions = []
    for t in agent_tools:
        # Parse out the name
        name = parse_tool_name(t)
        if name in TOOLS_REGISTRY:
            tool_functions.append(TOOLS_REGISTRY[name])
        else:
            print(f"Warning: No matching function found for tool '{t}'")

    # Prepare the dynamic variables.
    num_tools = len(agent_tools)
    # Create a bullet-point list from the tools.
    tools_list = "\n".join(f"   - {tool}" for tool in agent_tools)

    formatted_prompt = agent_cfg["prompt"].format(
        num_tools=num_tools,
        tools_list=tools_list,
        agents_list = all_agents
    )

    return {"model": agent_model, "prompt": formatted_prompt, "tools": tool_functions, "tool_description":agent_tools}
