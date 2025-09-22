# df-wrangler client (fixed) — copy me
import os
import platform
import logging

import requests
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
import pyperclip
from datetime import datetime

def print_generated_code_header():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    left_part = "[yellow]Generated Code: (Press Ctrl+Y to copy code)[/yellow]"
    right_part = f"[dim yellow]{timestamp}[/dim yellow]"
    left_plain_text_length = len(console.render_str(left_part, style=False))
    right_plain_text_length = len(console.render_str(right_part, style=False))
    current_console_width = console.width
    padding_needed = current_console_width - left_plain_text_length - right_plain_text_length
    if padding_needed < 1:
        padding_needed = 1
    final_string = f"{left_part}{' ' * padding_needed}{right_part}"
    console.print(f"\n{final_string}")

# Global variable to store the last generated code
last_generated_code = ""

# Configure logging
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "client.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file_path)],
)

console = Console()

# Define custom key bindings
kb = KeyBindings()


def forward_word_or_eol(buf):
    """If there's whitespace to the right -> next word start (WORD=True).
    Otherwise -> jump to end-of-line."""
    doc = buf.document
    after = doc.current_line_after_cursor
    n = doc.find_next_word_beginning(WORD=True)
    if any(ch.isspace() for ch in after) and n and n > 0:
        buf.cursor_position += n
    else:
        buf.cursor_position += doc.get_end_of_line_position()


def backward_word(buf):
    n = buf.document.find_start_of_previous_word(WORD=True)
    if n:
        buf.cursor_position += n


@kb.add(Keys.Escape, "b")  # Alt/Opt + b
def _(event):
    backward_word(event.current_buffer)


@kb.add(Keys.Escape, "f")  # Alt/Opt + f
def _(event):
    forward_word_or_eol(event.current_buffer)


@kb.add(Keys.ControlLeft)  # Ctrl + ←
def _(event):
    backward_word(event.current_buffer)


@kb.add(Keys.ControlRight)  # Ctrl + →
def _(event):
    forward_word_or_eol(event.current_buffer)


# Home / End helpers — NOTE: each decorator on its own line (no semicolons)
@kb.add("c-a")
@kb.add(Keys.Home)
def _(event):
    buf = event.current_buffer
    buf.cursor_position += buf.document.get_start_of_line_position()


@kb.add("c-e")
@kb.add(Keys.End)
def _(event):
    buf = event.current_buffer
    buf.cursor_position += buf.document.get_end_of_line_position()


@kb.add("c-y") # Ctrl+Y for copying code
def _(event):
    global last_generated_code
    if last_generated_code:
        try:
            pyperclip.copy(last_generated_code)
            console.print("[green]Generated code copied to clipboard.[/green]")
        except pyperclip.PyperclipException as e:
            console.print(f"[red]Error copying to clipboard: {e}[/red]")
    else:
        console.print("[yellow]No code to copy yet.[/yellow]")


# Initialize PromptSession with file history and custom key bindings
history_file = os.path.join(os.path.expanduser("~/"), ".df_wrangler_history")
session = PromptSession(history=FileHistory(history_file), key_bindings=kb)


def display_help():
    help_message = """
[bold blue]df-wrangler Help:[/bold blue]

[bold yellow]General Commands:[/bold yellow]
  - [green]exit[/green], [green]bye[/green], [green]stop[/green], [green]quit[/green]: Exit the application.
  - [green]help[/green]: Display this help message.

[bold yellow]Code Interaction:[/bold yellow]
  - Generated Python code is now displayed with syntax highlighting for better readability.
  - Press [green]Ctrl+Y[/green] to copy the last generated code to your clipboard.

[bold yellow]Dataframe Operations (Natural Language):[/bold yellow]
  - [green]Upload the file located at /path/to/your/data.csv[/green]
  - [green]Can you load the data from ./my_file.csv?[/green]
  - [green]What dataframes are currently loaded?[/green]
  - [green]Show df_my_data[/green] (to display the head of a dataframe)
  - [green]rename df_old to df_new[/green]
  - [green]remove df_to_delete[/green]
  - [green]pop[/green] (to revert to the previous state)
  - [green]What is the current working directory?[/green]
  - [green]Show me the column names of df_te that may contain datetimes.[/green]
  - [green]Create a new df called df_new that has all the rows from df_pr that are from the same date in Singapore local time that df_te rows are from. The column to be used to get the date is 'received_date_time'.[/green]

[bold blue]Remember to replace paths and dataframe names with your actual values.[/bold blue]
"""
    console.print(help_message)


while True:
    try:
        formatted_prompt = FormattedText([("ansibrightgreen bold", "df-wrangler> ")])
        user_input = session.prompt(formatted_prompt)

        if user_input.lower() in ["exit", "bye", "stop", "quit"]:
            console.print("[blue]Exiting df-wrangler. Goodbye![/blue]")
            break
        elif user_input.lower() == "help":
            display_help()
            continue

        response = requests.post("http://127.0.0.1:8000/command", json={"prompt": user_input})
        response.raise_for_status()
        server_response = response.json()

        if "action" in server_response and server_response["action"] == "upload":
            file_path = server_response.get("file_path")
            if file_path and os.path.exists(file_path):
                console.print(f"[yellow]Server requested upload of: {file_path}[/yellow]")
                with open(file_path, "rb") as f:
                    upload_response = requests.post("http://127.0.0.1:8000/execute_upload", files={"file": f})
                    upload_response.raise_for_status()
                    console.print(upload_response.json()["message"])
            else:
                console.print(f"[red]Error: File not found or path not provided by server: {file_path}[/red]")
        elif "plot_url" in server_response and "formatted_code" in server_response:
            plot_url = server_response.get("plot_url")
            code_content = server_response.get("code") # Get raw code
            formatted_code_content = server_response.get("formatted_code")
            last_generated_code = code_content # Store raw code
            console.print("[green]Your plot is ready. Please open this URL in your browser:[/green]")
            console.print(f"[bold blue]{plot_url}[/bold blue]")
            print_generated_code_header()
            syntax = Syntax(code_content, "python", theme="monokai", line_numbers=True)
            console.print(syntax)
        elif "plot_url" in server_response:
            # TODO: remove duplicate block
            plot_url = server_response.get("plot_url")
            console.print("[green]Your plot is ready. Please open this URL in your browser:[/green]")
            console.print(f"[bold blue]{plot_url}[/bold blue]")
        elif "download_url" in server_response:
            download_url = server_response.get("download_url")
            console.print("[green]Your file is ready. Please open this URL in your browser to download it:[/green]")
            console.print(f"[bold blue]{download_url}[/bold blue]")
        elif "error" in server_response:
            console.print(f"[red]Error from server: {server_response['error']}[/red]")
        elif "message" in server_response:
            console.print(f"[blue]{server_response['message']}[/blue]")
        elif "result" in server_response:
            if "formatted_code" in server_response:
                code_content = server_response.get("code") # Get raw code
                formatted_code_content = server_response.get("formatted_code")
                last_generated_code = code_content # Store raw code
                print_generated_code_header()
                syntax = Syntax(code_content, "python", theme="monokai", line_numbers=True)
                console.print(syntax)
            elif "code" in server_response: # Fallback if formatted_code is not present
                code_content = server_response.get("code") # Get raw code
                last_generated_code = code_content # Store raw code
                console.print("\n[yellow]Generated Code:[/yellow]")
                console.print(server_response["code"])
            console.print(f"\n[cyan]Result:[/cyan]") # Added a header for result
            console.print(f"[cyan]{server_response['result']}[/cyan]")
        else:
            console.print(f"[yellow]Unexpected server response: {server_response}[/yellow]")

    except KeyboardInterrupt:
        console.print("[yellow]Operation cancelled by user (Ctrl+C). Please try again.[/yellow]")
        continue
    except requests.exceptions.ConnectionError:
        console.print("[red]Error: Could not connect to the server. Is it running?[/red]")
        continue
    except requests.exceptions.RequestException as e:
        console.print(f"[red]An error occurred: {e}[/red]")
        continue
    except Exception as e:
        console.print(f"[red]An unexpected error occurred: {e}[/red]")
        continue
