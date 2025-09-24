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
import httpx
import asyncio
import time

# Server status feedback configuration
SERVER_PING_INTERVAL_SECONDS = 5
FAST_THRESHOLD_MS = 100
SLOW_THRESHOLD_MS = 500
SERVER_URL = "http://127.0.0.1:8000"  # Base URL for the server


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
client_logging_enabled = True
server_status_color = "green"  # Initial server status color


async def ping_server():
    global server_status_color
    start_time = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVER_URL}/health", timeout=SERVER_PING_INTERVAL_SECONDS)
            response.raise_for_status()
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            if latency_ms < FAST_THRESHOLD_MS:
                server_status_color = "green"
                # log.info(f"Server status: Green (Latency: {latency_ms:.2f}ms)")
            elif latency_ms < SLOW_THRESHOLD_MS:
                server_status_color = "orange"
                # log.info(f"Server status: Orange (Latency: {latency_ms:.2f}ms)")
            else:
                server_status_color = "red"  # Server is slow
                # log.info(f"Server status: Red (Latency: {latency_ms:.2f}ms - Slow)")
    except httpx.ConnectError:
        server_status_color = "red"  # Server is unreachable
        # log.info("Server status: Red (Unreachable)")
    except httpx.RequestError as e:
        server_status_color = "red"  # Other request errors
        # log.error(f"Server status: Red (Request Error: {e})")
    except Exception as e:
        # log.error(f"Error during server ping: {e}")
        server_status_color = "red"
        # log.info("Server status: Red (Unexpected Error)")


async def server_status_updater():
    while True:
        await ping_server()
        await asyncio.sleep(SERVER_PING_INTERVAL_SECONDS)


# Configure logging
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "client.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(module)s,%(lineno)d,%(message)s",
    handlers=[logging.FileHandler(log_file_path)],
)
# It's better to get the root logger and add a handler to it.
# This will ensure that logs from other libraries are also captured.
# Also, using RichHandler for colored output.
from rich.logging import RichHandler

log = logging.getLogger()
log.addHandler(RichHandler(rich_tracebacks=True))

# Suppress httpx internal logging to console
logging.getLogger("httpx").setLevel(logging.WARNING)

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


@kb.add("c-y")  # Ctrl+Y for copying code
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


async def main_loop():
    global server_status_color, client_logging_enabled
    # Start the server status updater as a background task
    asyncio.create_task(server_status_updater())

    while True:
        try:
            formatted_prompt = FormattedText([(server_status_color, "df-wrangler> ")])
            user_input = await asyncio.to_thread(session.prompt, formatted_prompt)
            if client_logging_enabled:
                logging.info(f"User prompt: {user_input}")

            if user_input.lower() in ["exit", "bye", "stop", "quit"]:
                console.print("[blue]Exiting df-wrangler. Goodbye![/blue]")
                break
            elif user_input.lower() == "help":
                display_help()
                continue

            response = await asyncio.to_thread(httpx.post, f"{SERVER_URL}/command", json={"prompt": user_input})
            response.raise_for_status()
            server_response = response.json()

            if "command" in server_response and server_response["command"] == "client_command":
                if client_logging_enabled:
                    logging.info(f"Server response: {server_response}")
                action = server_response.get("args", {}).get("action")
                if action == "disable_logging":
                    client_logging_enabled = False
                    console.print("[blue]Client logging disabled.[/blue]")
                elif action == "enable_logging":
                    client_logging_enabled = True
                    console.print("[blue]Client logging enabled.[/blue]")
            elif "action" in server_response and server_response["action"] == "upload":
                if client_logging_enabled:
                    logging.info(f"Server response: {server_response}")
                file_path = server_response.get("file_path")
                if file_path and os.path.exists(file_path):
                    console.print(f"[yellow]Server requested upload of: {file_path}[/yellow]")
                    with open(file_path, "rb") as f:
                        upload_response = await asyncio.to_thread(
                            httpx.post, f"{SERVER_URL}/execute_upload", files={"file": f}
                        )
                        upload_response.raise_for_status()
                        console.print(upload_response.json()["message"])
                else:
                    console.print(f"[red]Error: File not found or path not provided by server: {file_path}[/red]")
            elif "plot_url" in server_response and "formatted_code" in server_response:
                if client_logging_enabled:
                    logging.info(f"Server response: {server_response}")
                plot_url = server_response.get("plot_url")
                code_content = server_response.get("code")  # Get raw code
                formatted_code_content = server_response.get("formatted_code")
                last_generated_code = code_content  # Store raw code
                console.print("[green]Your plot is ready. Please open this URL in your browser:[/green]")
                console.print(f"[bold blue]{plot_url}[/bold blue]")
                print_generated_code_header()
                syntax = Syntax(code_content, "python", theme="monokai", line_numbers=True)
                console.print(syntax)
            elif "plot_url" in server_response:
                if client_logging_enabled:
                    logging.info(f"Server response: {server_response}")
                # TODO: remove duplicate block
                plot_url = server_response.get("plot_url")
                console.print("[green]Your plot is ready. Please open this URL in your browser:[/green]")
                console.print(f"[bold blue]{plot_url}[/bold blue]")
            elif "download_url" in server_response:
                if client_logging_enabled:
                    logging.info(f"Server response: {server_response}")
                download_url = server_response.get("download")
                console.print("[green]Your file is ready. Please open this URL in your browser to download it:[/green]")
                console.print(f"[bold blue]{download_url}[/bold blue]")
            elif "error" in server_response:
                if server_response.get("error") == "Prompt cannot be empty":
                    # Suppress output for empty prompts
                    pass
                else:
                    if client_logging_enabled:
                        logging.info(f"Server response: {server_response}")
                    console.print(f"[red]Error from server: {server_response['error']}[/red]")
            elif "message" in server_response:
                if client_logging_enabled:
                    logging.info(f"Server response: {server_response}")
                console.print(f"[blue]{server_response['message']}[/blue]")
            elif "result" in server_response:
                if client_logging_enabled:
                    logging.info(f"Server response: {server_response}")
                if "formatted_code" in server_response:
                    code_content = server_response.get("code")  # Get raw code
                    formatted_code_content = server_response.get("formatted_code")
                    last_generated_code = code_content  # Store raw code
                    print_generated_code_header()
                    syntax = Syntax(code_content, "python", theme="monokai", line_numbers=True)
                    console.print(syntax)
                elif "code" in server_response:  # Fallback if formatted_code is not present
                    code_content = server_response.get("code")  # Get raw code
                    last_generated_code = code_content  # Store raw code
                    console.print("\n[yellow]Generated Code:[/yellow]")
                    console.print(server_response["code"])
                console.print(f"\n[cyan]Result:[/cyan]")  # Added a header for result
                console.print(f"[cyan]{server_response['result']}[/cyan]")
            else:
                if client_logging_enabled:
                    logging.info(f"Server response: {server_response}")
                console.print(f"[yellow]Unexpected server response: {server_response}[/yellow]")

        except KeyboardInterrupt:
            console.print("[yellow]Operation cancelled by user (Ctrl+C). Please try again.[/yellow]")
            continue
        except httpx.ConnectError:
            console.print("[red]Error: Could not connect to the server. Is it running?[/red]")
            server_status_color = "red"  # Update status immediately on connection error
            continue
        except httpx.RequestError as e:
            console.print(f"[red]An HTTP request error occurred: {e}[/red]")
            server_status_color = "red"  # Update status immediately on request error
            continue
        except Exception as e:
            console.print(f"[red]An unexpected error occurred: {e}[/red]")
            continue


if __name__ == "__main__":
    asyncio.run(main_loop())
