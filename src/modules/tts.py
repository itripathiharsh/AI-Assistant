import os
import io
from gtts import gTTS
from pydub import AudioSegment
# from pydub.playback import play 

# ✅ Manually configure FFmpeg and FFprobe paths for Windows
AudioSegment.converter = r"C:\Users\imhar\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\Users\imhar\ffmpeg-7.1.1-essentials_build\bin\ffprobe.exe"

class TTSConnector:
    def __init__(self):
        print("✅ gTTS connector initialized.")

    def synthesize_speech(self, text, lang='en', play_audio=True, output_filename=None):
        """
        Synthesizes speech from text using gTTS.
        Args:
            text (str): The text to synthesize.
            lang (str): Language for synthesis (e.g., 'en', 'hi', 'mr', 'gu').
            play_audio (bool): Whether to play the audio after synthesis.
            output_filename (str): If provided, saves audio to this file.
                                   If None, a temporary file is created for playback.
        Returns:
            str: Path to saved audio file (if output_filename provided), else None.
        """
        if not text:
            print("⚠️ No text provided for synthesis.")
            return None

        print(f"🗣 Synthesizing speech in '{lang}' for text: '{text[:60]}...'")
        
        temp_file = False
        if not output_filename:
            output_filename = "temp_tts_audio.mp3"
            temp_file = True

        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(output_filename) 
            print(f"✅ Audio saved to: {output_filename}")
            
            if play_audio:
                try:
                    # Use os.startfile to play the audio with the system's default player
                    os.startfile(output_filename) 
                    print("🔊 Audio opened with system default player.")
                    # Give it a moment to start playing if it's a temp file, then clean up
                    if temp_file:
                        import time
                        time.sleep(1) # Give player a second to start
                        os.remove(output_filename)
                        print(f"Cleaned up temporary audio file: {output_filename}")

                except Exception as play_e:
                    print(f"❌ Error playing audio using os.startfile: {play_e}")
                    print("⚠️ Manual playback or troubleshooting system audio needed.")
            
            return output_filename if not temp_file else None 

        except Exception as e:
            print(f"❌ Error during TTS synthesis: {e}")
            if temp_file and os.path.exists(output_filename):
                os.remove(output_filename) 
            return None


# 🔧 Basic test (at the bottom of tts.py)
if __name__ == "__main__":
    try:
        # No need to import sounddevice explicitly here as we're not using pydub.playback.play
        # from pydub import AudioSegment is still needed by the class, ensure it's imported at top

        tts = TTSConnector()

        # English
        tts.synthesize_speech("Hello, I am Veena, your insurance assistant. How may I help you today?", lang='en', play_audio=True)

        # Hindi
        tts.synthesize_speech("नमस्ते, मैं वीणा हूँ। मैं आपकी क्या सहायता कर सकती हूँ?", lang='hi', play_audio=True)

        # Marathi
        tts.synthesize_speech("नमस्कार, मी वीणा. तुमची काय मदत करू शकतो?", lang='mr', play_audio=True)

        # Gujarati + save
        tts.synthesize_speech("નમસ્કાર, હું વીણા. તમારી શું મદદ કરી શકું છું?", lang='gu', play_audio=True, output_filename="test_gujarati.mp3")

    except Exception as e:
        print(f"❌ Unexpected error in TTS test script: {e}")