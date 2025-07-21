import os
from faster_whisper import WhisperModel

class STTConnector:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        """
        Initializes the Whisper model for Speech-to-Text.
        Args:
            model_size (str): "tiny", "base", "small", "medium", or "large-v2".
            device (str): "cpu" or "cuda".
            compute_type (str): "int8" for CPU, "float16" for GPU.
        """
        self.model = None
        try:
            print(f"🔄 Loading Whisper model '{model_size}' (device={device}, compute_type={compute_type})...")
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            print("✅ Whisper model loaded successfully.")
        except Exception as e:
            print(f"❌ Error loading Whisper model: {e}")

    def transcribe_audio(self, audio_file_path):
        """
        Transcribes a real speech-based audio file to text.
        Returns:
            str: Transcribed text or None.
        """
        if not self.model:
            print("❌ Whisper model not initialized.")
            return None

        if not os.path.exists(audio_file_path):
            print(f"❌ Audio file not found: {audio_file_path}")
            return None

        print(f"🎧 Transcribing: {audio_file_path}")
        try:
            segments, _ = self.model.transcribe(audio_file_path, beam_size=5)
            transcript = " ".join([seg.text for seg in segments])
            return transcript.strip() if transcript else None
        except Exception as e:
            print(f"❌ Error during transcription: {e}")
            return None

# ---------- Run test with a real WAV file ---------- #
if __name__ == "__main__":
    test_audio_path = r"D:\\downloads\\HIN_M_AbhishekS.mp3"  

    stt_connector = STTConnector(model_size="base")  
    transcribed_text = stt_connector.transcribe_audio(test_audio_path)

    if transcribed_text:
        print(f"✅ Transcribed Text:\n'{transcribed_text}'")
    else:
        print("⚠️ No speech detected or STT test failed. Please use a valid voice audio file.")
