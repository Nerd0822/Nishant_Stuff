import os
import google.generativeai as genai


genai.configure(api_key="AIzaSyA8lxY26RFM-ArWAHq4cJ5ESjTjfjV8-yM")

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
)

def generate(text):
    response = model.generate_content([
    "you are a ai virtual guide chatbot named wanderAI.so reply accordingly with least words if possible but explaining in an detailed manner and in an friendly manner",
    f"input: {text}",
    "output: ", 
    ])

    return response.text


    