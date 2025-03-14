import pyttsx3
import speech_recognition as sr

#for speech recognition
def hear_me_out():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        text = recognizer.recognize_google(audio)
    
    except sr.UnknownValueError:
        pass
    
    except sr.RequestError:
        pass
        
    return text
    
# for text to speech
def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    engine.setProperty("voice",voices[1].id)
    engine.setProperty("rate",140)

    engine.say(text)
    engine.runAndWait()