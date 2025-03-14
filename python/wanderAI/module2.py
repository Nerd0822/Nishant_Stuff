api_key="AIzaSyA8lxY26RFM-ArWAHq4cJ5ESjTjfjV8-yM"

import google.generativeai as genai

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-flash")

def generate():
  try:
  
    response = model.generate_content("mandi, himachal pradesh")

  except Exception as e:
    pass
  
  return response