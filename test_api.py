# simpan sebagai test_api.py lalu python test_api.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "Halo, apa kabar?"}],
    max_tokens=50
)

print(response.choices[0].message.content)