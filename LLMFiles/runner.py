import speech_recognition as sr

r = sr.Recognizer()
with sr.AudioFile('demo-audio.opus') as source:
    audio_data = r.record(source)
    text = r.recognize_google(audio_data)
    print(text)
