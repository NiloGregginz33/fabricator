import os
import sys
import time
import openai
import tempfile
import requests
import speech_recognition as sr
from pydub import AudioSegment
from octorest import OctoRest
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

octoprint_address = 'https://octopi.local'
api_key = '{put octopi api key here}'

def make_client(url, apikey):
     """Creates and returns an instance of the OctoRest client.

     Args:
         url - the url to the OctoPrint server
         apikey - the apikey from the OctoPrint server found in settings
     """
     try:
         client = OctoRest(url=url, apikey=apikey)
         return client
     except ConnectionError as ex:
         # Handle exception as you wish
         print(ex)


def print_gcode_file(filename, octoprint_address, api_key):

    filename = filename + ".gcode"
    
    folder_path = "models/"
    file_path = os.path.join(folder_path, filename)
    
    if not os.path.isfile(file_path):
        print(f"Error: File {filename} not found in {folder_path}")
        return
    
    octo = make_client(url=octoprint_address, apikey=api_key)
    upload = octo.upload(file_path)

    print(upload)

    file_url = upload['files']['local']['name']
    filename = upload['files']['local']['refs']['resource']
    print(file_url)
    print(filename)
    

    octo.select(file_url)


    response = octo.start()
    settings = octo.settings()
    print(settings)
    octo.tool_target(230)
    


def extract_nouns(sentence):
    sentence = sentence.replace('Hey Jarvis', '')
    
    words = word_tokenize(sentence)
    
    tagged_words = pos_tag(words)
    nouns = [word for word, pos in tagged_words if pos.startswith('N')]
    
    return nouns[2]

openai.api_key = '{put openai api key here}'

BUFFER_DURATION = 5  
TRIGGER_PHRASE = 'hey jarvis'
REQUEST_DELAY = 1 

def transcribe_whisper(audio_file_path):
    with open(audio_file_path, "rb") as audio_file: 
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    print(transcript)
    return transcript["text"]

def listen_and_transcribe():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")

        while True:
            audio_data = recognizer.record(source, duration=BUFFER_DURATION)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                temp_audio_file.write(audio_data.get_wav_data())

            transcription = transcribe_whisper(temp_audio_file.name)
            print(f"Transcription: {transcription}")
            os.remove(temp_audio_file.name)

            if TRIGGER_PHRASE.lower() in transcription.lower():
                print(f"Trigger phrase '{TRIGGER_PHRASE}' detected!")
                # Add your desired action here
                sentence = transcription.lower()
                nouns = extract_nouns(sentence)
                print(nouns)
                print_gcode_file(nouns, octoprint_address, api_key)
                

            time.sleep(REQUEST_DELAY)

if __name__ == "__main__":
    listen_and_transcribe()