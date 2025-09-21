import openai
import os
import json
import re
from datetime import datetime
from .dataframe_service import dataframe_service
from .code_execution_service import code_execution_service
from .milvus_service import milvus_service
from .logging_service import logging_service

class LLMService:
    def __init__(self, config):
        self.config = config
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = self.config.llm.model

    def log(self, message):
        if logging_service.get_logging_level("llm") == "on":
            log_file = logging_service.get_log_file("llm")
            if log_file:
                with open(log_file, "a", buffering=1) as f: # buffering=1 for line-buffering
                    f.write(f"{datetime.now().strftime(\%Y-%m-%d %H:%M:%S,%f\")} - INFO - [LLMService] {message}")
            else:
                print(f"[LLMService] {message}")

    def _get_classification_prompt(self, user_prompt: str) -> str:
        prompt_template = """You are a command interpreter for a data analysis chatbot.
Your task is to analyze the user's prompt and classify it into one of the following commands and extract its arguments.
You must respond in JSON format ONLY, with no additional text or explanations, and no markdown.

The available commands are:
- 'upload': For loading a CSV file. This command is used when the user explicitly mentions a file path or a file name to be loaded.
- 'rename': For renaming a dataframe. Requires 'old_name' and 'new_name'.
- 'pop': For reverting to the previous state. Requires no arguments.
- 'remove': For removing a dataframe. Requires 'df_name'.
- 'download': For downloading a dataframe to a CSV file. Requires 'df_name' and an optional 'filename'.
- 'list_dataframes': For listing all currently loaded dataframes. Requires no arguments.
- 'analyze': For any other data analysis task that involves querying or manipulating loaded dataframes. The original prompt is passed through.
- 'set_logging': For turning logging on or off for a specific service or all services. Requires 'service_name' (e.g., "llm", "dataframe", "all") and 'level' (e.g., "on", "off").
- 'list_services': For listing all available services.
- 'service_health': For getting the health of a specific service or all services.

Here are some examples:

User prompt: "upload data/my_file.csv"
Your response:
{"command": "upload", "args": {"file_path": "data/my_file.csv"}}

User prompt: "show the list of uploaded files"
Your response:
{"command": "list_dataframes", "args": {}}

User prompt: "rename df_old to df_new"
Your response:
{"command": "rename", "args": {"old_name": "df_old", "new_name": "df_new"}}

User prompt: "pop"
Your response:
{"command": "pop", "args": {}}

User prompt: "remove the dataframe named 'old_data'"
Your response:
{"command": "remove", "args": {"df_name": "old_data"}}

User prompt: "Show me the first 5 rows of df_my_data"
Your response:
{"command": "analyze", "args": {"prompt": "Show me the first 5 rows of df_my_data"}}

User prompt: "download my_df as report.csv"
Your response:
{"command": "download", "args": {"df_name": "my_df", "filename": "report.csv"}}

User prompt: "download my_df"
Your response:
{"command": "download", "args": {"df_name": "my_df", "filename": "my_df.csv"}}

User prompt: "turn on logging for the llm service"
Your response:
{"command": "set_logging", "args": {"service_name": "llm", "level": "on"}}

User prompt: "turn off logging for all services"
Your response:
{"command": "set_logging", "args": {"service_name": "all", "level": "off"}}

User prompt: "list all services"
Your response:
{"command": "list_services", "args": {}}

User prompt: "what is the health of the dataframe service?"
Your response:
{"command": "service_health", "args": {"service_name": "dataframe"}}

User prompt: "show me the health of all services"
Your response:
{"command": "service_health", "args": {"service_name": "all"}}
"""
        return f"""{prompt_template}{user_prompt}
Your response:
"""

    def classify_and_extract_command(self, prompt: str) -> dict:
        """
        Uses the LLM to classify the prompt and extract arguments.
        """
        full_prompt = self._get_classification_prompt(prompt)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{'role': 'user', 'content': full_prompt}],
            temperature=0.0,  # We want deterministic output
        )

        try:
            return json.loads(response.choices[0].message.content)
        except (json.JSONDecodeError, KeyError, IndexError):
            return {"command": "analyze", "args": {"prompt": prompt}}

    def _get_dataframe_context(self, prompt: str) -> str:
        """
        Get the context of the dataframe mentioned in the prompt.
        """
        df_names = list(dataframe_service.get_all_dataframes().keys())
        if not df_names:
            return ""

        # Search for the most relevant dataframe schema
        search_results = milvus_service.search_dataframe_schemas(prompt)
        if search_results:
            return search_results[0]['schema_text']

        # Fallback to the old logic if no relevant schema is found
        df_name = None
        for name in df_names:
            if name in prompt:
                df_name = name
                break

        if not df_name:
            df_name = df_names[0]

        df = dataframe_service.get_dataframe(df_name)
        if df is None:
            return ""

        context = f"""Here is the context for the dataframe `{df_name}`:

**Columns and Data Types:**
{df.dtypes.to_string()}

**First 5 rows:**
{df.head().to_string()}
"""
        return context

    def generate_code(self, prompt: str) -> (bool, str):
        """
        Generates Python/pandas code from a user prompt.
        """
        self.log(f"--- Code Generation Prompt (User Input) ---\n{prompt}\n---")

        # Get context from Milvus
        dataframe_context = self._get_dataframe_context(prompt)
        examples = milvus_service.search_examples(prompt)
        history = milvus_service.search_conversation_history(prompt)

        examples_context = ""
        if examples:
            examples_context = "\nRelevant Examples:\n" + "\n".join(examples)

        history_context = ""
        if history:
            history_context = """
Relevant Conversation History:
"""
            for turn in history:
                history_context += f"User: {turn['prompt']}\nCode: {turn['code']}\nResult: {turn['result']}\n"

        prompt_template = f"""You are "DataWrangler", a friendly and helpful AI assistant that helps users analyze data with pandas. You are an expert in pandas and you always generate correct and efficient code.

You have access to the following tools:
- `dataframe_service`: An object to manage dataframes. Use `dataframe_service.get_dataframe("df_name")` to get a dataframe.
- `results_history`: A list of the results of the last 10 commands. `results_history[-1]` is the most recent result.
- `last_result`: A convenient alias for `results_history[-1]`.
- `plots_dir`: The absolute path to the directory where plots should be saved.

**Your Task:**
Your task is to generate a single block of Python code to answer the user's prompt. The result of your code MUST be assigned to a variable named `result`.

**Golden Rules:**
1.  **Always be helpful and friendly.**
2.  **Always generate correct and efficient pandas code.**
3.  **Always use the tools provided.**
4.  **Self-Contained Code:** For any new analysis, you MUST generate a self-contained block of code. Do NOT rely on `last_result` unless the user's prompt explicitly refers to the previous result (e.g., "from these results...", "with this data...").
5.  **NEVER generate code that is not related to data analysis with pandas.**
6.  **NEVER use `print()` statements.**
7.  **NEVER explain the code.** Just generate the code block.
8.  **If the result is a single-row pandas Series or DataFrame, ensure it is transposed to be displayed horizontally.**

**How to Handle Common Scenarios:**

*   **Single Row Output:** If your result is a single-row Series or DataFrame, transpose it to ensure horizontal display.
    *   **Example:** `result = df.loc[index].to_frame().T`

*   **Filtering DataFrames:** When you need to filter a DataFrame based on a condition, you should create a boolean mask and apply it to the DataFrame.
    *   **Example:**
        ```python
        mask = df['some_column'] > some_value
        result = df[mask]
        ```

*   **Data Cleaning:** Before any numeric operations, you MUST inspect the columns and if they contain non-numeric characters, you MUST clean them and convert them to a numeric type.
    *   **Example:** `df['col'] = pd.to_numeric(df['col'].str.replace(r'[^0-9.]', '', regex=True), errors='coerce')`

*   **Numeric Operations (General):** For operations that require numeric data (e.g., `.corr()`, `.sum()`, `.mean()`), you should operate on numeric columns only. You can select numeric columns using `df.select_dtypes(include=np.number)`.
    *   **Example (Correlation):**
        ```python
        import numpy as np
        numeric_df = df.select_dtypes(include=np.number)
        correlation_matrix = numeric_df.corr()
        ```

*   **Concatenating Series:** To concatenate multiple pandas Series, you MUST use `pd.concat()`. NEVER use `Series.append()`.
    *   **Example:** `all_numbers = pd.concat([df['num1'], df['num2'], df['num3']])`

*   **Formatting `value_counts()` output:** When you use `value_counts()` to find common numbers, don't return the raw Series object. Convert it to a dictionary or a list of tuples to make it more readable.
    *   **Example:** `result = number_counts[number_counts > 1].to_dict()`

*   **Finding Common Numbers:** When you need to find common numbers, get the number columns dynamically.
    *   **Example:**
        ```python
        number_columns = [col for col in last_result.columns if col.startswith('num')]
        numbers = last_result[number_columns].melt(value_name='number')['number']
        # ...
        ```

*   **Plotting:**
    1.  **You MUST import `os` before using it to construct file paths.**
    2.  **NEVER use `plt.show()`.** It will crash the application. You MUST save the plot to a file.
    3.  The `result` variable MUST be set to the absolute path of the saved plot file.
    4.  **Example:**
        ```python
        import matplotlib.pyplot as plt
        import os
        plt.figure()
        plt.plot([1, 2, 3])
        plot_filename = 'my_plot.png'
        plot_path = os.path.join(plots_dir, plot_filename)
        plt.savefig(plot_path)
        result = plot_path
        ```

*   **Calculating and Plotting Deviation:** When asked to plot the deviation of a set of numbers, you should first calculate the standard deviation for each row, and then plot the histogram of these standard deviations.
    *   **Example:**
        ```python
        import matplotlib.pyplot as plt
        number_columns = [col for col in df.columns if col.startswith('num')]
        df['std_dev'] = df[number_columns].std(axis=1)
        plt.figure()
        plt.hist(df['std_dev'], bins=20)
        plt.title('Histogram of Standard Deviation')
        plot_path = 'storage/plots/std_dev_histogram.png'
        plt.savefig(plot_path)
        result = plot_path
        ```

*   **Using Previous Results:** If the user's prompt refers to a previous result (e.g., "from these numbers"), you MUST use the `results_history` list.
    *   **Example:**
        *   User: "show me the top 5 rows from df_my_data based on the 'score' column"
        *   You generate: `result = dataframe_service.get_dataframe("df_my_data").nlargest(5, 'score')`
        *   User: "from these, show me the ones with a score greater than 50"
        *   You generate: `result = last_result[last_result['score'] > 50]`
        *   User: "now show me the top 10 from the original dataframe"
        *   You generate: `result = dataframe_service.get_dataframe("df_my_data").nlargest(10, 'score')`
        *   User: "from the first result, show me the ones with a score less than 30"
        *   You generate: `result = results_history[-3][results_history[-3]['score'] < 30]`

*   **Multiple Rows for Max/Min:** When asked for rows with maximal or minimal values, ensure all matching rows are returned. Do not use `idxmax()` or `idxmin()` directly to select rows if multiple rows could share the same maximal/minimal value. Instead, filter the DataFrame.
    *   **Example (General Max/Min):**
        ```python
        max_value = df['column_name'].max()
        result = df[df['column_name'] == max_value]
        ```
    *   **Example (Max/Min Difference between Consecutive Rows):** When asked for rows that show the maximal or minimal difference between a value and its previous value, identify the index of the maximal/minimal difference, and then return both the row at that index and the preceding row.
        ```python
        df['diff_column'] = df['value_column'] - df['value_column'].shift(1)
        max_diff_index = df['diff_column'].idxmax()
        result = df.loc[[max_diff_index - 1, max_diff_index]]
        ```

*   **Ambiguous Prompts:** If the user's prompt is ambiguous (e.g., "this number"), you MUST look at the `results_history` to infer the context.
    *   **Example:**
        *   `results_history` contains a dictionary as the last result: `{33: 2}`
        *   User: "how many times did this number appear in the previous result?"
        *   You generate:
            ```python
            number_to_check = list(last_result.keys())[0]
            dataframe_to_search = results_history[-2]
            numbers = dataframe_to_search[['num1', 'num2', 'num3', 'num4', 'num5']].melt(value_name='number')['number']
            number_counts = numbers.value_counts()
            result = number_counts.get(number_to_check, 0)
            ```


Now, let's get to work! The user is waiting for your amazing code.
"""
        
        system_prompt = f"{prompt_template}\n\n{dataframe_context}{examples_context}{history_context}\n\n"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt,
                },
                {
                    'role': 'user',
                    'content': prompt,
                }
            ]
        )
        raw_code = response.choices[0].message.content
        self.log(f"--- Raw LLM Response ---\n{raw_code}\n---")
        
        match = re.search(r'```(?:python\n)?(.*?)(?:```|$)', raw_code, re.DOTALL)
        if match:
            code = match.group(1).strip()
            code = code.replace("dataframeservice", "dataframe_service")
            code = code.replace(
                "dataframe_service.get_all_dataframes().keys()", "list(dataframe_service.get_all_dataframes().keys())"
            )
            return (True, code.strip())
        else:
            return (False, raw_code)

    def health(self):
        # For now, we'll just check if the OpenAI API key is set
        if os.getenv("OPENAI_API_KEY"):
            return "OK"
        else:
            return "Error: OPENAI_API_KEY not set"