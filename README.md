# df-wrangler

`df-wrangler` is a CLI chatbot application designed for interactive data analysis. It uses a FastAPI backend and a command-line client to allow users to upload CSV files, manipulate them as pandas DataFrames using natural language prompts, and receive results directly in the terminal.

The application leverages OpenAI with the `gpt-4o-mini` model to interpret user commands and generate executable Python/pandas code. The code generation has been made more robust to handle general queries and common LLM output variations.

## Features

-   **CLI Interface**: Interact with your data using a simple, prompt-based command line, built with `rich` and `prompt_toolkit` for history.
-   **CSV Upload**: Easily upload multiple CSV files, which are automatically loaded into pandas DataFrames.
-   **Natural Language Processing**: Translates complex analytical prompts into Python/pandas code using OpenAI (gpt-4o-mini). The LLM (OpenAI gpt-4o-mini) also interprets general commands like `upload` and `rename`.
-   **Persistent & Versioned Storage**: DataFrame states are automatically saved after each operation. You can "pop" back to a previous state, providing a version history.
-   **Extensible & Scalable**: Built with FastAPI and designed to be easily scalable, with considerations for deployment via Ray Serve.
-   **Server-side Prompt Logging**: User prompts sent to the LLM are now logged on the server for debugging and monitoring purposes.
-   **Tested**: Includes unit tests (unittest) and property-based tests (Hypothesis).

## Project Structure

```
/df-wrangler
├── client/             # CLI client application
│   ├── main.py
│   ├── pyproject.toml
│   └── setup.sh
├── server/             # FastAPI backend server
│   ├── app/
│   │   ├── api/        # API endpoints
│   │   ├── conf/       # Hydra configuration (config.yaml)
│   │   ├── core/       # Core logic and config loading
│   │   ├── schemas/    # Pydantic models
│   │   ├── services/   # Business logic for dataframes, LLM, storage
│   │   └── main.py     # FastAPI app entrypoint
│   ├── storage/        # Directory for pickled dataframe states
│   ├── tests/          # Unit and property-based tests
│   ├── .env            # Environment variables
│   ├── pyproject.toml
│   └── setup.sh
└── README.md           # This file
```

## 1. Installation & Setup

This project uses `uv` to manage dependencies.

### Prerequisites

-   Python 3.13
-   [uv](https://github.com/astral-sh/uv) installed.
-   [gpt-4o-mini](https://platform.openai.com/) configured.

### Server Setup

1.  **Navigate to the server directory:**
    ```bash
    cd server
    ```

2.  **Run the setup script:**
    ```bash
    ./setup.sh
    ```
    This will create a `.venv` directory, activate it, and install the required Python packages.

### Client Setup

1.  **Navigate to the client directory:**
    ```bash
    cd client
    ```

2.  **Run the setup script:**
    ```bash
    ./setup.sh
    ```

## 2. Configuration





## 3. Running the Application

You will need two separate terminal windows to run the server and the client.

### Start the Server

1.  **Navigate to the server directory and activate the virtual environment:**
    ```bash
    cd server
    source .venv/bin/activate
    ```

2.  **Start the FastAPI server with Uvicorn:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The server is now running and accessible at `http://127.0.0.1:8000`.

### Start the Client

1.  **In a new terminal, navigate to the client directory and activate the virtual environment:**
    ```bash
    cd client
    source .venv/bin/activate
    ```

2.  **Run the client application:**
    ```bash
    python main.py
    ```
    You will see the `df-wrangler>` prompt. The client now supports prompt history (use up/down arrow keys).

## 4. Operation (How to Use)

Interact with the application by typing commands at the `df-wrangler>` prompt. The LLM will interpret your intent for all commands, allowing for more natural phrasing. Below are numbered examples that can be used as a walkthrough or as test cases.

### Example Workflow

#### Uploading CSV files

1.  `Upload the file located at /path/to/your/dashboard_pr.csv`
    *   *Result: The server will instruct the client to upload the file, and a dataframe named `df_dashboard_pr` will be created. The path should start from the project root.*

2.  `Can you load the data from ./data/dashboard_te.csv?`
    *   *Result: The server will instruct the client to upload the file, and a dataframe named `df_dashboard_te` will be created.*

3.  `Use the file named 'sample.csv' in the current directory`
    *   *Result: The server will instruct the client to upload the file, and a dataframe named `df_sample` will be created.*

#### Basic Analysis

4.  `Show the shape of df_dashboard_pr`
    *   *Result: Displays the number of rows and columns in the dataframe.*

5.  `How many lines are there?`
    *   *Result: Displays the number of rows in the first loaded dataframe.*

6.  `List the column names of df_dashboard_te`
    *   *Result: Shows the headers of all columns.*

#### Renaming DataFrames

6.  `Rename df_dashboard_pr to df_pr`
    *   *Result: The dataframe is now accessible as `df_pr`.*

7.  `I want to rename df_dashboard_te to df_te`
    *   *Result: The dataframe is now accessible as `df_te`.*

#### More Advanced Prompts

8.  `Show me the column names of df_te that may contain datetimes. They may have the type of string, but contain datetimes.`
    *   *Result: The LLM will analyze column names and content to identify potential datetime columns.*

9.  `Create a new df called df_new that has all the rows from df_pr that are from the same date in Singapore local time that df_te rows are from. The column to be used to get the date is 'received_date_time'.`
    *   *Result: Executes a complex join/filter operation and creates a new dataframe `df_new`.*

10. `What are the data types of the columns in df_new?`
    *   *Result: Displays the pandas `dtypes` for the newly created dataframe.*

11. `Show a histogram where the x axis is the weeks (rows) and the y axis is the sum of the winning numbers for that week.`
    *   *Result: Displays a histogram of the sum of winning numbers per week, saved as a PNG file.*

#### Reverting State with Pop

12. `Pop the last change`
    *   *Result: The creation of `df_new` is undone. The application state is reverted to before command #9 was executed.*

13. `Undo the previous operation`
    *   *Result: The rename of `df_te` is undone. The dataframe is now named `df_dashboard_te` again.*