### Passo 1: Crie o Diretório e o Ambiente Virtual
Abra o Terminal (Ctrl+Alt+T) e rode esses comandos um por um:
Crie e entre no diretório do app
```sh
mkdir ~/audio_to_srt_app
cd ~/audio_to_srt_app
```
### Crie o venv (usa Python nativo do Ubuntu)
```sh
python3 -m venv venv
```
### Ative o venv (faça isso sempre antes de rodar o app)
```sh
source venv/bin/activate
```
Agora, todos os comandos seguintes serão dentro desse venv ativado.

### Passo 2: Instale as Dependências
Ainda no Terminal (com venv ativado):
Atualize pip e instale pacotes essenciais
```sh
pip install -U pip setuptools wheel
```
### Instale faster-whisper (para transcrição rápida no CPU)
```sh
pip install faster-whisper
```
### Instale ffmpeg-python (para lidar com formatos de áudio como mp3/m4a/ogg)
```sh
pip install ffmpeg-python
```
### Instale Tkinter se não vier pré-instalado (geralmente vem, mas para garantir)
```sh
sudo apt update
sudo apt install python3-tk
```
### Instale o ffmpeg completo (obrigatório para processar áudios variados):
```sh
sudo apt install ffmpeg
```
Isso deve levar 5-15 minutos, dependendo da sua conexão. Se der erro de permissão, use sudo para os apt.

### Instale Argos Translate (dentro do venv)
No terminal (com source venv/bin/activate):
```sh
pip install argostranslate
```
Na primeira vez, ele baixa o pacote de modelo en → pt automaticamente (~500 MB, leva uns minutos na primeira execução). Depois fica cacheado.
### Instale: 
```sh
pip install deep-translator
```
### Instale a lib (no venv ativado)
```sh
pip install gTTS
```
### Instale pydub (no venv ativado)
```sh
pip install pydub
sudo apt install ffmpeg  # já deve ter, mas garante
```
### Instale no venv:
```sh
pip install TTS
```
### Crie o Script Python do App
No diretório ~/audio_to_srt_app, crie um arquivo chamado app.py (use nano ou seu editor favorito):
```sh
nano app.py
```
### Rode o App
No Terminal (com venv ativado: source venv/bin/activate):
```sh
python app.py
```
Uma janela vai abrir.
Clique em "Carregar Áudio" → selecione seu .mp3/.m4a/.ogg.
Aguarde a transcrição (o status atualiza; em CPU fraca, um áudio de 5 min pode levar 1-3 min).
Quando pronto, o .srt é gerado na mesma pasta do áudio.
Clique em "Baixar SRT" → escolha onde salvar (cópia do arquivo gerado).

### Dicas para Sua Máquina Fraca

Se demorar muito na transcrição: Mude MODEL_SIZE = "small.en" no script e teste.
RAM alta? Feche outros apps; faster-whisper usa ~3-5 GB no medium.en.
Erro? Verifique se ffmpeg está instalado (ffmpeg -version) e me mande o erro.
Para rodar sempre: Ative venv e python app.py.


### Como funciona agora:

Carrega áudio → transcreve em inglês (SRT _en.srt).
Traduz linha por linha para PT-BR (offline) → gera _pt.srt.
Botão "Baixar SRT" salva o em português.
Na primeira tradução, baixa o modelo Argos en-pt (só uma vez).

## Transformando em app executável
### Sugestão top 1 (mais simples e free forever): GitHub Releases

Coloque o código no GitHub (repo privado ou público).
Use PyInstaller pra gerar executável Linux/Windows:
```sh
pip install pyinstaller
pyinstaller --onefile --windowed app.py
```
O executável fica na pasta dist/.
Faça upload do executável + README no GitHub Releases.
Compartilha o link com amigos — eles baixam e rodam sem instalar nada.

### Se quiser web (acesso pelo browser):

Converta pra Streamlit (troque Tkinter por Streamlit widgets) → suba no Streamlit Cloud free.
