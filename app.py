import tkinter as tk
from tkinter import filedialog, messagebox
from faster_whisper import WhisperModel
from datetime import timedelta
import os
import subprocess
from deep_translator import GoogleTranslator
from pydub import AudioSegment

# ======================
# PIPER CONFIGURAÇÃO
# ======================
PIPER_CMD = ["python", "-m", "piper"]
PIPER_MODEL = os.path.expanduser(
    "~/.local/share/piper/pt_BR-faber-medium.onnx"
)

# < 1.0 = fala mais rápida (valor seguro)
PIPER_LENGTH_SCALE = "0.88"
PIPER_SENTENCE_SILENCE = "0.12"

# ======================
# WHISPER CONFIGURAÇÃO
# ======================
MODEL_SIZE = "medium.en"
COMPUTE_TYPE = "int8"
LANGUAGE = "en"

translator = GoogleTranslator(source="en", target="pt")

# ======================
# UTILITÁRIOS
# ======================
def format_time(seconds):
    td = timedelta(seconds=seconds)
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    secs = td.seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def parse_srt_time(time_str):
    time_str = time_str.replace(",", ".")
    h, m, s = time_str.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)

# ======================
# GERADOR DE SRT
# ======================
def generate_srt(segments, output_path, translate=False):
    texts = [seg.text.strip() for seg in segments]

    translated = texts
    if translate:
        try:
            translated = translator.translate_batch(texts)
        except Exception:
            pass

    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = format_time(seg.start)
            end = format_time(seg.end)
            f.write(f"{i}\n{start} --> {end}\n{translated[i - 1]}\n\n")

# ======================
# PIPER + SINCRONIZAÇÃO (SEM SPEEDUP)
# ======================
def generate_timed_audio(pt_srt_path):
    segments = []
    current = {}

    with open(pt_srt_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.isdigit():
                current = {}
            elif "-->" in line:
                s, e = line.split(" --> ")
                current["start"] = parse_srt_time(s)
                current["end"] = parse_srt_time(e)
                current["text"] = ""
            elif line:
                current["text"] += line + " "
            elif current:
                segments.append(current)

    combined = AudioSegment.silent(duration=0)
    prev_end = 0.0

    for i, seg in enumerate(segments):
        text = seg["text"].strip()
        if not text:
            continue

        target_ms = int((seg["end"] - seg["start"]) * 1000)
        temp_wav = f"seg_{i}.wav"

        cmd = [
            *PIPER_CMD,
            "--model", PIPER_MODEL,
            "--length_scale", PIPER_LENGTH_SCALE,
            "--sentence-silence", PIPER_SENTENCE_SILENCE,
            "--output_file", temp_wav,
        ]

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        _, err = proc.communicate(text)
        if proc.returncode != 0:
            raise RuntimeError(f"Piper erro:\n{err}")

        audio = AudioSegment.from_wav(temp_wav)
        os.remove(temp_wav)

        # silêncio até início do segmento
        gap_ms = int((seg["start"] - prev_end) * 1000)
        if gap_ms > 0:
            combined += AudioSegment.silent(duration=gap_ms)

        # REGRA DE OURO:
        # nunca esticar áudio — só cortar ou completar com silêncio
        if len(audio) > target_ms:
            audio = audio[:target_ms]

        combined += audio

        remainder = target_ms - len(audio)
        if remainder > 0:
            combined += AudioSegment.silent(duration=remainder)

        prev_end = seg["end"]

    # pequeno buffer final
    combined += AudioSegment.silent(duration=500)

    output = pt_srt_path.replace("_pt.srt", "_pt_timed_audio.wav")
    combined.export(output, format="wav")
    return output

# ======================
# PIPELINE PRINCIPAL
# ======================
def transcribe_audio(audio_file):
    try:
        status_label.config(text="Carregando Whisper...")
        root.update()

        model = WhisperModel(
            MODEL_SIZE,
            device="cpu",
            compute_type=COMPUTE_TYPE,
        )

        status_label.config(text="Transcrevendo...")
        root.update()

        segments, _ = model.transcribe(
            audio_file,
            language=LANGUAGE,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        segments = list(segments)

        base = os.path.splitext(audio_file)[0]
        en_srt = base + "_en.srt"
        pt_srt = base + "_pt.srt"

        generate_srt(segments, en_srt)
        status_label.config(text="Traduzindo...")
        root.update()

        generate_srt(segments, pt_srt, translate=True)

        status_label.config(text="Gerando áudio PT sincronizado...")
        root.update()

        audio = generate_timed_audio(pt_srt)

        status_label.config(
            text=f"Pronto!\n\n{en_srt}\n{pt_srt}\n{audio}"
        )

    except Exception as e:
        messagebox.showerror("Erro", str(e))
        status_label.config(text="Erro. Veja o terminal.")

# ======================
# UI
# ======================
def load_audio():
    file = filedialog.askopenfilename(
        title="Selecione áudio",
        filetypes=[("Áudio", "*.mp3 *.m4a *.wav *.ogg *.mp4 *.opus *.aac")],
    )
    if file:
        transcribe_audio(file)

root = tk.Tk()
root.title("Audio → SRT + Narração PT-BR (WAV sincronizado)")
root.geometry("520x230")

tk.Button(
    root,
    text="Carregar Áudio",
    font=("Arial", 14),
    width=26,
    command=load_audio,
).pack(pady=45)

status_label = tk.Label(
    root,
    text="Pronto.",
    wraplength=480,
    font=("Arial", 10),
)
status_label.pack(pady=20)

root.mainloop()
