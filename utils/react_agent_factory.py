# agent_factory.py
from typing import Literal

from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langgraph.types import Command
from langgraph.graph import MessagesState
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from utils.utils import get_agent_config

def create_agent_node(agent_name: str, default_goto: str = "supervisor"):
    """
    Creates and returns a node function for a given agent_name.
    Each returned node function can be used in the state graph.
    """
    # Load the config based on the agent name
    agent_config = get_agent_config(agent_name)
    agent_prompt = agent_config["prompt"]
    agent_tools = agent_config["tools"]
    agent_model = agent_config["model"]

    memory = MemorySaver()

    # Create the LLM and the agent
    agent_llm = ChatOllama(model=agent_model)
    agent = create_react_agent(
        agent_llm,
        tools=agent_tools,
        prompt=agent_prompt,
        checkpointer=memory
    )

    def node_func(state: MessagesState) -> Command[Literal[default_goto]]:
        """
        If you want your subagents to use the whole state then use:
        
        result = agent.invoke(state)

        If you want your subagents to focus on the supervisors message only which is useful when using cheaper models, then use:

        #result = agent.invoke({"messages": [("user", state["messages"][-1].content)]})
        """

        result = agent.invoke(state)
        
        return Command(
            update={
                "messages": [
                    AIMessage(
                        content=result["messages"][-1].content, 
                        name=agent_name
                    )
                ]
            },
            goto=default_goto
        )

    return node_func