import pyttsx3
import speech_recognition as sr
import datetime
import pyaudio
import wikipedia
import webbrowser
import os


engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')

#print(voices)



def speak_boy(audio):
    engine.setProperty('voice' , voices[0].id)
    engine.say(audio)
    engine.runAndWait()

    
def speak(audio):
    engine.setProperty('voice' , voices[0].id)
    engine.say(audio)
    engine.runAndWait()
    
def speak_girl(audio):
    engine.setProperty('voice' , voices[1].id)
    engine.say(audio)
    engine.runAndWait()
    
    

def WishMe():
    hour = int(datetime.datetime.now().hour)
    if hour>=0 and hour<12:
        speak_girl("Hello!, Good Morning.")
    if hour>=12 and hour<18:
        speak_girl("Hello!, Good Afternoon.")
    else:
        speak_girl("Hello!, Good Evening.")
    speak_boy("I am Pranav. How Can I help you?")



def takeCommand():
    r=sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio=r.listen(source)

    try:
        print("Recognizing...")
        query = r.recognize_google(audio, Language='en-in')
        print(f"User said: {query}\n")
    
    except Exception as e:
        #print(e)
        print("Say that again please...")
        return "None"
    return query
        





#WishMe()




#takeCommand()


if __name__ == "__main__":
    WishMe()
    while True:
        query = takeCommand().lower()
        if 'wikipedia' in query:
            speak('Searching Wikipedia...')
            query = query.replace("Wekipedia" , "")
            results = wikipedia.summary(query, sentences=2)
            speak("According to Wikipedia")
            print(results)
            speak(results)

        elif 'open youtube' in query:
            webbrowser.open("youtube.com")
        elif 'open google' in query:
            webbrowser.open("google.com")
        elif 'open your website Pranav' in query:
            webbrowser.open("pranavmahadkar.tech")
        elif 'open stackoverflow' in query:
            webbrowser.open("stackoverflow.com")
        elif 'play music' in query:
            # directory. i dont like music
            print("no music")
        elif 'the time' in query:
            strTime = datetime.date.now().strftime("%H:%M:&S")
            speak(f"The time is {strTime}")
            print(strTime)


           






















































 
