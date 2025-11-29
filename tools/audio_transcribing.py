import os
from langchain.tools import tool
import speech_recognition as sr
from pydub import AudioSegment

@tool
def transcribe_audio(file_path: str) -> str:
    """
    Converts audio file content to text using Google Web Speech API.

    Supports both MP3 and WAV formats. MP3 files are automatically converted to
    WAV format before transcription. Temporary WAV files are cleaned up after
    processing.

    Args:
        file_path (str): Relative path to audio file (.mp3 or .wav)

    Returns:
        str: Transcribed text content or error message

    Dependencies:
        - pydub: For audio format conversion
        - speech_recognition: For transcription
        - Internet connection: Required for Google API
    """
    try:
        # Build full path to audio file
        full_path = os.path.join("LLMFiles", file_path)
        working_path = full_path
        
        # Handle MP3 to WAV conversion if necessary
        if full_path.lower().endswith(".mp3"):
            audio_segment = AudioSegment.from_mp3(full_path)
            working_path = full_path.replace(".mp3", ".wav")
            audio_segment.export(working_path, format="wav")

        # Perform speech-to-text transcription
        speech_recognizer = sr.Recognizer()
        with sr.AudioFile(working_path) as audio_source:
            recorded_audio = speech_recognizer.record(audio_source)
            transcription = speech_recognizer.recognize_google(recorded_audio)

        # Clean up temporary WAV file if it was created
        if working_path != full_path and os.path.exists(working_path):
            os.remove(working_path)

        return transcription
    except Exception as error:
        return f"Error occurred: {error}"