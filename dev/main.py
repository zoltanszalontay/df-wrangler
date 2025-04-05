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
agent_b = DiscussionAgent(name="B", color="cyan")

default_system_prompt_a = agent_a.agent.system_prompt_generator.generate_prompt()
console.print(Panel(default_system_prompt_a, width=console.width, style="bold red"), style="bold red")

default_system_prompt_b = agent_b.agent.system_prompt_generator.generate_prompt()
console.print(Panel(default_system_prompt_b, width=console.width, style="bold cyan"), style="bold cyan")


# Start an infinite loop to handle user inputs and agent responses
response_a = "Is it possible to make a time machine?"
for i in range(5):
    if i == 0:
        response_b = agent_b.get_response(response_a)
    else:
        response_b = agent_b.get_response(response_a._text[0])
    console.print(Text(f"{agent_b.name}:", style=f"bold {agent_b.color}"), end=" ")
    console.print(response_b)

    response_a = agent_a.get_response(response_b._text[0])
    console.print(Text(f"{agent_a.name}:", style=f"bold {agent_a.color}"), end=" ")
    console.print(response_a)
