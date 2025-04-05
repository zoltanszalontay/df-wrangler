import os
from openai import OpenAI as OllamaClient
import instructor
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema


class DiscussionAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.memory = AgentMemory()
        self.setup_client()
        self.agent = BaseAgent(
            config=BaseAgentConfig(
                client=self.client, model=self.model, memory=self.memory, model_api_parameters={"max_tokens": 2048}
            )
        )
        # Initialize memory with an initial message from the assistant
        initial_message = BaseAgentOutputSchema(chat_message="Hello! How can I assist you today?")
        self.memory.add_message("assistant", initial_message)
        self.console = Console()

    def setup_client(self):
        self.client = instructor.from_openai(
            OllamaClient(base_url="http://localhost:11434/v1", api_key="ollama"), mode=instructor.Mode.JSON
        )
        self.model = "phi3:medium"

    def get_response(self, prompt):
        input_schema = BaseAgentInputSchema(chat_message=prompt)
        response = self.agent.run(input_schema)
        self.response = Text(response.chat_message, style=f"bold {self.color}")
        return self.response
