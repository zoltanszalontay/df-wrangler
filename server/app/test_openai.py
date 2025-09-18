import os
import openai


def test_openai_connectivity():
    """
    Tests connectivity to the OpenAI API using an API key from an environment variable.
    """
    print("Attempting to connect to the OpenAI API...")

    try:
        # 1. Get the API key from environment variables
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY environment variable not set.")
            print("Please set the variable, for example: export OPENAI_API_KEY='your_key_here'")
            return

        # In newer versions of the openai library, you initialize a client
        client = openai.OpenAI(api_key=api_key)

        # 2. Make a simple API call to test connectivity (listing models is a good, low-cost choice)
        print("API key found. Making a test call to list models...")
        response = client.models.list()

        # 3. Check if we received any data
        if response.data:
            print("\nSuccessfully connected to the OpenAI API!")
            print(f"Found {len(response.data)} models. The first model is: {response.data[0].id}")
        else:
            print("Connection successful, but no models were found.")

    except openai.AuthenticationError:
        print("\nError: Authentication failed. Your API key is likely invalid or expired.")
        print("Please check your OpenAI API key and ensure it is set correctly.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("This could be a network issue or a problem with the OpenAI service.")


if __name__ == "__main__":
    test_openai_connectivity()


#
