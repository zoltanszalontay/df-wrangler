import os
import sys

# Add the server's app directory to the Python path to resolve imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from services.milvus_service import milvus_service

def populate_examples():
    """
    Populates the Milvus database with code generation examples.
    """
    examples = [
        "*   **Single Row Output:** If your result is a single-row Series or DataFrame, transpose it to ensure horizontal display.\n    *   **Example:** `result = df.loc[index].to_frame().T`",
        "*   **Filtering DataFrames:** When you need to filter a DataFrame based on a condition, you should create a boolean mask and apply it to the DataFrame.\n    *   **Example:**\n        ```python\n        mask = df['some_column'] > some_value\n        result = df[mask]\n        ```",
        "*   **Data Cleaning:** Before any numeric operations, you MUST inspect the columns and if they contain non-numeric characters, you MUST clean them and convert them to a numeric type.\n    *   **Example:** `df['col'] = pd.to_numeric(df['col'].str.replace(r'[^0-9.]', '', regex=True), errors='coerce')`",
        "*   **Numeric Operations (General):** For operations that require numeric data (e.g., `.corr()`, `.sum()`, `.mean()`), you should operate on numeric columns only. You can select numeric columns using `df.select_dtypes(include=np.number)`.\n    *   **Example (Correlation):**\n        ```python\n        import numpy as np\n        numeric_df = df.select_dtypes(include=np.number)\n        correlation_matrix = numeric_df.corr()\n        ```",
        "*   **Concatenating Series:** To concatenate multiple pandas Series, you MUST use `pd.concat()`. NEVER use `Series.append()`.\n    *   **Example:** `all_numbers = pd.concat([df['num1'], df['num2'], df['num3']])`",
        "*   **Formatting `value_counts()` output:** When you use `value_counts()` to find common numbers, don't return the raw Series object. Convert it to a dictionary or a list of tuples to make it more readable.\n    *   **Example:** `result = number_counts[number_counts > 1].to_dict()`",
        "*   **Finding Common Numbers:** When you need to find common numbers, get the number columns dynamically.\n    *   **Example:**\n        ```python\n        number_columns = [col for col in last_result.columns if col.startswith('num')]\n        numbers = last_result[number_columns].melt(value_name='number')['number']\n        # ...\n        ```",
        "*   **Plotting:**\n    1.  **You MUST import `os` before using it to construct file paths.**\n    2.  **NEVER use `plt.show()`.** It will crash the application. You MUST save the plot to a file.\n    3.  The `result` variable MUST be set to the absolute path of the saved plot file.\n    4.  **Example:**\n        ```python\n        import matplotlib.pyplot as plt\n        import os\n        plt.figure()\n        plt.plot([1, 2, 3])\n        plot_filename = 'my_plot.png'\n        plot_path = os.path.join(plots_dir, plot_filename)\n        plt.savefig(plot_path)\n        result = plot_path\n        ```",
        "*   **Calculating and Plotting Deviation:** When asked to plot the deviation of a set of numbers, you should first calculate the standard deviation for each row, and then plot the histogram of these standard deviations.\n    *   **Example:**\n        ```python\n        import matplotlib.pyplot as plt\n        number_columns = [col for col in df.columns if col.startswith('num')]\n        df['std_dev'] = df[number_columns].std(axis=1)\n        plt.figure()\n        plt.hist(df['std_dev'], bins=20)\n        plt.title('Histogram of Standard Deviation')\n        plot_path = 'storage/plots/std_dev_histogram.png'\n        plt.savefig(plot_path)\n        result = plot_path\n        ```",
        "*   **Using Previous Results:** If the user's prompt refers to a previous result (e.g., \"from these numbers\"), you MUST use the `results_history` list.\n    *   **Example:**\n        *   User: \"show me the top 5 rows from df_my_data based on the 'score' column\"\n        *   You generate: `result = dataframe_service.get_dataframe(\"df_my_data\").nlargest(5, 'score')`\n        *   User: \"from these, show me the ones with a score greater than 50\"\n        *   You generate: `result = last_result[last_result['score'] > 50]`",
        "*   **Multiple Rows for Max/Min:** When asked for rows with maximal or minimal values, ensure all matching rows are returned. Do not use `idxmax()` or `idxmin()` directly to select rows if multiple rows could share the same maximal/minimal value. Instead, filter the DataFrame.\n    *   **Example (General Max/Min):**\n        ```python\n        max_value = df['column_name'].max()\n        result = df[df['column_name'] == max_value]\n        ```\n    *   **Example (Max/Min Difference between Consecutive Rows):** When asked for rows that show the maximal or minimal difference between a value and its previous value, identify the index of the maximal/minimal difference, and then return both the row at that index and the preceding row.\n        ```python\n        df['diff_column'] = df['value_column'] - df['value_column'].shift(1)\n        max_diff_index = df['diff_column'].idxmax()\n        result = df.loc[[max_diff_index - 1, max_diff_index]]\n        ```",
        "*   **Ambiguous Prompts:** If the user's prompt is ambiguous (e.g., \"this number\"), you MUST look at the `results_history` to infer the context.\n    *   **Example:**\n        *   `results_history` contains a dictionary as the last result: `{33: 2}`\n        *   User: \"how many times did this number appear in the previous result?\"\n        *   You generate:\n            ```python\n            number_to_check = list(last_result.keys())[0]\n            dataframe_to_search = results_history[-2]\n            numbers = dataframe_to_search[['num1', 'num2', 'num3', 'num4', 'num5']].melt(value_name='number')['number']\n            number_counts = numbers.value_counts()\n            result = number_counts.get(number_to_check, 0)\n            ```"
    ]

    # Check if the collection is already populated
    if milvus_service.client.query("code_examples", "count(*) == 0")[0]['count'] == 0:
        print("Populating the 'code_examples' collection...")
        for example in examples:
            milvus_service.add_example(example)
        print("Population complete.")
    else:
        print("The 'code_examples' collection is already populated.")

if __name__ == "__main__":
    populate_examples()
