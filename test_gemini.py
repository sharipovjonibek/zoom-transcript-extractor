import os
import google.generativeai as genai
from dotenv import load_dotenv

# load env variables
load_dotenv()

# get api key
API_KEY = os.getenv("GEMINI_API_KEY")

# configure gemini
genai.configure(api_key=API_KEY)

# choose model
model = genai.GenerativeModel("gemini-3-flash-preview")

# send prompt
response = model.generate_content(
    "Who is Lochinbek, he study at university of INHA in Tashkent, and he is a software engineer, and he is a good person?"
)

print("\nGemini response:\n")
print(response.text)