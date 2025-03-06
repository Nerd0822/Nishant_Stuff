from flask import Flask, request, jsonify
from flask_cors import CORS
import module1
import module2

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

@app.route('/chat', methods=['POST'])
def chat():
    """Handles text input from the frontend and returns AI response."""
    try:
        data = request.get_json()
        user_input = data.get("message", "").strip()
        
        if not user_input:
            return jsonify({"error": "Empty message"}), 400

        ai_response = module2.generate(user_input)
        return jsonify({"response": ai_response})

    except Exception as e:
        print(f"Error in /chat: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/voice-chat', methods=['GET'])
def voice_chat():
    """Handles voice input, converts to text, gets AI response, and speaks it."""
    try:
        user_input = module1.record_and_convert()
        
        if "error" in user_input.lower():
            return jsonify({"error": user_input}), 400
        
        ai_response = module2.generate(user_input)
        module1.speak(ai_response)  # Speak the response
        
        return jsonify({"response": ai_response})

    except Exception as e:
        print(f"Error in /voice-chat: {e}")
        return jsonify({"error": "Internal server error please try again"}), 500

if __name__ == '__main__':
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"Critical Error: {e}")


#to do : fix the ai response in you said and learn how the code even words.
# also implement google translate and weather forecast , google maps
# implement a feature to plan the trip along with weather forecast, map to show direction, images of the place you want to visit and a translate feature
#also if possible make an mobile app