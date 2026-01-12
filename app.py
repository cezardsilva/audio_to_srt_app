import tkinter as tk
from tkinter import filedialog, messagebox
from faster_whisper import WhisperModel
from datetime import timedelta
import os
from deep_translator import GoogleTranslator
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play  # opcional, só para teste

# Configurações
MODEL_SIZE = "medium.en"
COMPUTE_TYPE = "int8"
LANGUAGE = "en"

translator = GoogleTranslator(source='en', target='pt')

def format_time(seconds):
    td = timedelta(seconds=seconds)
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    secs = td.seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def generate_srt(segments, output_path, translate=False):
    with open(output_path, "w", encoding="utf-8") as f:
        if translate:
            texts = [seg.text.strip() for seg in segments]
            try:
                translated_batch = translator.translate_batch(texts)
            except Exception as e:
                print(f"Erro batch: {e}")
                translated_batch = [t + " [falha]" for t in texts]
        for i, segment in enumerate(segments, 1):
            start = format_time(segment.start)
            end = format_time(segment.end)
            text = translated_batch[i-1] if translate and translated_batch else segment.text.strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    # print(f"SRT gerado: {output_path} ({os.path.getsize(output_path)} bytes)")

def parse_srt_time(time_str):
    """Converte 'HH:MM:SS,mmm' ou 'HH:MM:SS.mmm' para segundos float"""
    time_str = time_str.replace(',', '.')  # Trata vírgula como ponto decimal
    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        return 0.0
    except Exception as e:
        print(f"Erro parseando tempo '{time_str}': {e}")
        return 0.0

def generate_timed_audio(pt_srt_path):
    """Gera MP3 com pausas baseadas nos timestamps do SRT PT-BR"""
    try:
        segments = []
        current = {'start': 0.0, 'end': 0.0, 'text': ''}
        with open(pt_srt_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    if current['text'].strip():
                        segments.append(current)
                    current = {'start': 0.0, 'end': 0.0, 'text': ''}
                    continue
                if '-->' in line:
                    start_str, end_str = [t.strip() for t in line.split(' --> ')]
                    current['start'] = parse_srt_time(start_str)
                    current['end'] = parse_srt_time(end_str)
                    continue
                if line:
                    current['text'] += line + " "

        # Último segmento
        if current['text'].strip():
            segments.append(current)

        if not segments:
            raise ValueError("Nenhum segmento válido encontrado no SRT.")

        print(f"Encontrados {len(segments)} segmentos para narração.")

        combined = AudioSegment.silent(duration=0)
        prev_end = 0.0

        for idx, seg in enumerate(segments):
            text = seg['text'].strip()
            if not text:
                continue

            print(f"Segmento {idx+1}: '{text[:60]}...' (início {seg['start']}s)")

            tts = gTTS(
                text=text,          # texto limpo, sem tags!
                lang='pt',
                slow=False,         # velocidade normal (a mais rápida)
                tld='com.br'        # sotaque BR mais natural
            )
            temp_mp3 = f"temp_seg_{idx}.mp3"
            tts.save(temp_mp3)

            seg_audio = AudioSegment.from_mp3(temp_mp3)

            # Calcula gap (pausa) entre o fim do anterior e o início deste
            gap_seconds = seg['start'] - prev_end
            gap_ms = max(0, int(gap_seconds * 1000))  # não negativo
            if gap_ms > 0:
                combined += AudioSegment.silent(duration=gap_ms)
            else:
                # Se overlap ou consecutivo, adiciona pequeno buffer
                combined += AudioSegment.silent(duration=300)  # 0.3s para respiração natural

            combined += seg_audio
            prev_end = seg['end']

            os.remove(temp_mp3)  # Limpa arquivo temporário

        audio_path = pt_srt_path.replace("_pt.srt", "_pt_timed_audio.mp3")
        combined.export(audio_path, format="mp3")
        size = os.path.getsize(audio_path)
        print(f"Áudio temporizado gerado: {audio_path} ({size} bytes)")

        return audio_path

    except Exception as e:
        print(f"Erro ao gerar áudio temporizado: {e}")
        return None

def transcribe_audio(audio_file):
    try:
        status_label.config(text="Carregando Whisper...")
        root.update()

        model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE, cpu_threads=0)

        status_label.config(text="Transcrevendo...")
        root.update()

        segments, info = model.transcribe(audio_file, language=LANGUAGE, beam_size=5, vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500))
        segments = list(segments)

        en_srt = os.path.splitext(audio_file)[0] + "_en.srt"
        generate_srt(segments, en_srt, translate=False)

        pt_srt = os.path.splitext(audio_file)[0] + "_pt.srt"
        status_label.config(text="Traduzindo...")
        root.update()
        generate_srt(segments, pt_srt, translate=True)

        status_label.config(text="Gerando narração PT-BR com timing...")
        root.update()
        audio_path = generate_timed_audio(pt_srt)

        status_label.config(text=f"Pronto!\nSRT EN: {en_srt}\nSRT PT: {pt_srt}\nÁudio PT temporizado: {audio_path or 'falhou'}")

    except Exception as e:
        messagebox.showerror("Erro", str(e))
        status_label.config(text="Erro. Veja terminal.")

def load_audio():
    audio_file = filedialog.askopenfilename(title="Selecione áudio", filetypes=[("Áudio", "*.mp3 *.m4a *.ogg *.wav *.mp4 *.opus")])
    if audio_file:
        status_label.config(text=f"Carregado: {os.path.basename(audio_file)}")
        transcribe_audio(audio_file)

root = tk.Tk()
root.title("Audio → SRT + Narração PT-BR Temporizada")
root.geometry("500x220")

load_button = tk.Button(root, text="Carregar Áudio", command=load_audio, font=("Arial", 14), width=25)
load_button.pack(pady=50)

status_label = tk.Label(root, text="Pronto para começar. (Internet necessária)", wraplength=450, font=("Arial", 10))
status_label.pack(pady=20)

root.mainloop()