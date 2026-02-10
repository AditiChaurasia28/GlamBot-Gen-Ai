from dotenv import load_dotenv
import os

load_dotenv()
print(os.getenv("GROQ_API_KEY"))
from groq import Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

res = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role":"user","content":"hello"}],
    max_tokens=5
)

print(res.choices[0].message.content)
