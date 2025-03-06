#importing libraries
import speech_recognition as sr
import pyttsx3

voice = 1 # 0 male and 1 female
speed = 150


#recording voice and the convert it into text
def record_and_convert(): #method to record and convert the speech to text
    speech_recog=sr.Recognizer()
    with sr.Microphone() as mic:
        print("Speak now....")
        speech_recog.adjust_for_ambient_noise(mic) # to reduce noises in the voice
        speech = speech_recog.listen(mic,timeout=5,phrase_time_limit=30)
        
    try:
        text = speech_recog.recognize_google(speech) #convert to text
        print("you said: ",text)
        return text
    except sr.UnknownValueError:
        print("sorry can you repeat that again")
        
    except sr.RequestError:
        print("count not request results.")
        
    return "" # returning an empty string when any error occurs
        
    
    
#method to speak
def speak(txt):
    engine = pyttsx3.init()
    
    #get the list of all available voices
    voices = engine.getProperty("voices")
    
    #applying the voice property
    engine.setProperty("voice",voices[voice].id)
    engine.setProperty("rate",speed)
    
    engine.say(txt)
    engine.runAndWait()
    