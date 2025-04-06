import os
from openai import OpenAI as OllamaClient
import instructor
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema


class DiscussionAgent:
    def __init__(self, name: str, color: str, system_prompt_generator=None):
        self.name = name
        self.color = color
        self.system_prompt_generator = system_prompt_generator
        self.memory = AgentMemory()
        self.setup_client()
        self.agent = BaseAgent(
            config=BaseAgentConfig(
                client=self.client,
                model=self.model,
                memory=self.memory,
                model_api_parameters={"max_tokens": 2048},
                system_prompt_generator=self.system_prompt_generator,
            )
        )
        # Initialize memory with an initial message from the assistant
        initial_message = BaseAgentOutputSchema(chat_message="I am a helpful assistant.")
        self.memory.add_message("assistant", initial_message)
        self.console = Console()

    def setup_client(self):
        self.client = instructor.from_openai(
            OllamaClient(base_url="http://localhost:11434/v1", api_key="ollama"), mode=instructor.Mode.JSON
        )
        self.model = "phi3:mini"

    def get_response(self, prompt):
        input_schema = BaseAgentInputSchema(chat_message=prompt)
        response = self.agent.run(input_schema)
        self.response = Text(response.chat_message, style=f"bold {self.color}")
        return self.response


if __name__ == "__main__":
    agent = DiscussionAgent(name="Discussion Agent", color="blue")

    # First prompt
    prompt = "What is the capital of France?"
    response = agent.get_response(prompt)

    # Display the first response in a rich panel
    panel = Panel(response, title=agent.name, border_style=agent.color)
    agent.console.print(panel)

    # Forward the first response back to the agent as a new prompt
    follow_up_prompt = f"The agent said: '{response.plain}' Can you elaborate on that?"
    follow_up_response = agent.get_response(follow_up_prompt)

    # Display the follow-up response in a rich panel
    follow_up_panel = Panel(follow_up_response, title=f"{agent.name} (Follow-Up)", border_style=agent.color)
    agent.console.print(follow_up_panel)
