import requests

# Ollama runs on this URL by default
OLLAMA_URL = "http://localhost:11434/api/generate"

# Define the prompt
payload = {"model": "phi3:mini", "prompt": "Explain what gravity is in simple terms.", "stream": False}

# Send the request
response = requests.post(OLLAMA_URL, json=payload)
response.raise_for_status()  # Raise if error

# Print the generated text
result = response.json()
print("🤖:", result.get("response"))
