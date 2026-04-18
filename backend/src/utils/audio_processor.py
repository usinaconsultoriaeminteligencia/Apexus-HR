from .advanced_voice_analysis import analyze_interview_audio

class AudioProcessor:
    """
    Stub do processador de áudio.
    M2: ligar Whisper (OpenAI ou faster-whisper) e métricas (librosa/soundfile).
    """
    def analyze_audio(self, path: str) -> dict:
        return analyze_interview_audio(path)

    def transcribe_audio(self, path: str) -> str:
        return "Transcrição (stub): implementar STT na próxima iteração."
