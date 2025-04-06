import os
import logging
from openai import OpenAI as OllamaClient
from pydantic import Field
import instructor
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from dotenv import load_dotenv

from agent import DiscussionAgent


def setup_logger(name="df-wrangler", log_file="app.log"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(log_file, mode="w")
        fh.setLevel(logging.INFO)
        # ch = logging.StreamHandler()
        # ch.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s")
        fh.setFormatter(formatter)
        # ch.setFormatter(formatter)
        logger.addHandler(fh)
        # logger.addHandler(ch)
    return logger


log_file = "./logs/df-wrangler.log"
logger = setup_logger(log_file=log_file)
logger.info("Logger initialized")


load_dotenv()

console = Console()


system_prompt_generator_a = SystemPromptGenerator(
    background=[
        "This assistant is a scientist that always question the user's responses.",
        "Always challenges the user with relevant questions in the current scientific topic.",
    ],
    steps=[
        "Understand the user's input",
        "Respond with a question that develops the innovative conversation.",
    ],
    output_instructions=[
        "Your response always contains a feedback to the user's response followed by a question to clarify the response.",
        "Always refer to scientific facts.",
        "Respond with a concise answer not longer than one paragraph.",
    ],
)

system_prompt_generator_b = SystemPromptGenerator(
    background=[
        "This assistant is an innovator AI designed to find new ways to achieve new things. It is a creative thinker.",
    ],
    steps=[
        "Understand the user's input, which question, and prepare an innovative response.",
        "Respond to the user.",
    ],
    output_instructions=[
        "Provide helpful and relevant information to assist the user.",
        "Always think out of the box, innovate and find new ways to do things.",
        "Always respond with a concise answer not longer than one paragraph.",
    ],
)


agent_a = DiscussionAgent(name="A", color="red", system_prompt_generator=system_prompt_generator_a)
agent_b = DiscussionAgent(name="B", color="blue", system_prompt_generator=system_prompt_generator_b)

default_system_prompt_a = agent_a.agent.system_prompt_generator.generate_prompt()
console.print(Panel(default_system_prompt_a, width=console.width, style="bold red"), style="bold red")

default_system_prompt_b = agent_b.agent.system_prompt_generator.generate_prompt()
console.print(Panel(default_system_prompt_b, width=console.width, style="bold blue"), style="bold blue")

# Start an infinite loop to handle user inputs and agent responses
initial_message = "How would you make a timemachine?"
console.print(Text(f"Initial message: {initial_message}", style=f"bold {agent_a.color}"))
response_a = None
response_b = None

for i in range(5):
    response_b = agent_b.get_response(initial_message if i == 0 else response_a.plain)
    console.print(Text(f"{agent_b.name}:", style=f"bold {agent_b.color}"), end=" ")
    console.print(response_b.plain)
    logger.info(f"{agent_b.name}: {response_b.plain}")

    response_a = agent_a.get_response(response_b.plain)
    console.print(Text(f"{agent_a.name}:", style=f"bold {agent_a.color}"), end=" ")
    console.print(response_a.plain)
    logger.info(f"{agent_a.name}: {response_a.plain}")
