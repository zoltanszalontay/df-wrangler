import os
from openai import OpenAI as OllamaClient
import instructor
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema
from dotenv import load_dotenv

from agent import DiscussionAgent

load_dotenv()

console = Console()

agent_a = DiscussionAgent(name="A", color="red")
agent_b = DiscussionAgent(name="B", color="blue")

default_system_prompt_a = agent_a.agent.system_prompt_generator.generate_prompt()
console.print(Panel(default_system_prompt_a, width=console.width, style="bold red"), style="bold red")

default_system_prompt_b = agent_b.agent.system_prompt_generator.generate_prompt()
console.print(Panel(default_system_prompt_b, width=console.width, style="bold blue"), style="bold blue")


# Start an infinite loop to handle user inputs and agent responses
prompt = "Hello! How can I assist you today?"
response_a = None
response_b = None

for i in range(5):
    response_b = agent_b.get_response(prompt if i == 0 else response_a.plain)
    console.print(Text(f"{agent_b.name}:", style=f"bold {agent_b.color}"), end=" ")
    console.print(response_b.plain)

    response_a = agent_a.get_response(response_b.plain)
    console.print(Text(f"{agent_a.name}:", style=f"bold {agent_a.color}"), end=" ")
    console.print(response_a.plain)
