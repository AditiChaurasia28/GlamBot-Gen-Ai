from groq import Groq
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": "Give one fashion styling tip for casual wear."}
        ]
    )

    print("Groq API Connected Successfully ✅")
    print("Response:", response.choices[0].message.content)

except Exception as e:
    print("Groq API Connection Failed ❌")
    print(e)
