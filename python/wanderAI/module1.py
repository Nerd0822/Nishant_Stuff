import speech_recognition as sr
import pyttsx3

voice = 1  # 0 male and 1 female
speed = 150

def record_and_convert():
    """Records voice and converts it to text."""
    speech_recog = sr.Recognizer()
    
    try:
        with sr.Microphone() as mic:
            print("Speak now....")
            speech_recog.adjust_for_ambient_noise(mic)
            speech = speech_recog.listen(mic, timeout=5, phrase_time_limit=30)
        
        text = speech_recog.recognize_google(speech)
        
        return text

    except sr.UnknownValueError:
        print("Sorry, I couldn't understand. Please repeat.")
        return "error: could not understand speech"
    
    except sr.RequestError:
        print("Network error. Please check your internet connection.")
        return "error: network issue"

    except OSError:
        print("Microphone not accessible. Please check your device.")
        return "error: microphone issue"
    
    return ""

def speak(txt):
    """Speaks out the given text."""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        engine.setProperty("voice", voices[voice].id)
        engine.setProperty("rate", speed)
        engine.say(txt)
        engine.runAndWait()
    except Exception as e:
        print("Speech synthesis error:", str(e))
