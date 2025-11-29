
from pydub import AudioSegment

opus_file = "demo-audio.opus"
wav_file = "demo-audio.wav"

audio = AudioSegment.from_file(opus_file, format="opus")
audio.export(wav_file, format="wav")
print("Conversion complete!")
