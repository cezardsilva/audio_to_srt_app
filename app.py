import tkinter as tk
from tkinter import filedialog, messagebox
from faster_whisper import WhisperModel
from datetime import timedelta
import os

# Configurações fixas (para inglês, CPU fraca)
MODEL_SIZE = "small.en"  # Mude para "small.en" se for muito lento
COMPUTE_TYPE = "int8"     # Otimizado para CPU
LANGUAGE = "en"

def format_time(seconds):
    td = timedelta(seconds=seconds)
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    secs = td.seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def generate_srt(segments, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, 1):
            start = format_time(segment.start)
            end = format_time(segment.end)
            text = segment.text.strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    return output_path

def transcribe_audio(audio_file):
    try:
        status_label.config(text="Carregando modelo... (pode demorar um pouco na primeira vez)")
        root.update()
        
        model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE, cpu_threads=0)
        
        status_label.config(text="Transcrevendo... (aguarde, depende do tamanho do áudio)")
        root.update()
        
        segments, info = model.transcribe(
            audio_file,
            language=LANGUAGE,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        
        output_srt = os.path.splitext(audio_file)[0] + ".srt"
        generated_file = generate_srt(segments, output_srt)
        
        status_label.config(text=f"Pronto! SRT gerado: {generated_file}")
        download_button.config(state=tk.NORMAL)  # Ativa o botão de download
        global current_srt
        current_srt = generated_file
        
    except Exception as e:
        messagebox.showerror("Erro", f"Falha na transcrição: {str(e)}")
        status_label.config(text="Erro na transcrição.")

def load_audio():
    audio_file = filedialog.askopenfilename(
        title="Selecione o arquivo de áudio",
        filetypes=[("Arquivos de áudio", "*.mp3 *.m4a *.ogg *.wav")]
    )
    if audio_file:
        status_label.config(text=f"Áudio carregado: {os.path.basename(audio_file)}")
        transcribe_audio(audio_file)

def download_srt():
    if 'current_srt' in globals():
        save_path = filedialog.asksaveasfilename(
            defaultextension=".srt",
            filetypes=[("SRT files", "*.srt")],
            initialfile=os.path.basename(current_srt)
        )
        if save_path:
            with open(current_srt, 'rb') as f_in, open(save_path, 'wb') as f_out:
                f_out.write(f_in.read())
            messagebox.showinfo("Sucesso", f"SRT salvo em: {save_path}")
    else:
        messagebox.showwarning("Aviso", "Gere o SRT primeiro!")

# Interface gráfica simples
root = tk.Tk()
root.title("Audio to SRT App")
root.geometry("400x200")

load_button = tk.Button(root, text="Carregar Áudio", command=load_audio)
load_button.pack(pady=20)

download_button = tk.Button(root, text="Baixar SRT", command=download_srt, state=tk.DISABLED)
download_button.pack(pady=10)

status_label = tk.Label(root, text="Pronto para carregar áudio.", wraplength=350)
status_label.pack(pady=10)

root.mainloop()