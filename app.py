import subprocess
import os
import json
import gradio as gr
from pydub import AudioSegment
from header import badges, description
from pydub.silence import split_on_silence
from get_voices import get_voices
#from adjust import remove_silence, controlador_generate_audio, generate_audio

# Load voices from JSON file
def load_voices():
    with open('voices.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# Get formatted voice options for specific language
def get_voice_options(language, voices_data):
    if language in voices_data:
        return [f"{voice['name']} | {voice['gender']}" for voice in voices_data[language]]
    return []

# Extract voice name from formatted string
def extract_voice_name(formatted_voice):
    return formatted_voice.split(" | ")[0]

def update_voice_options(language):
    voices_data = load_voices()
    voice_options = get_voice_options(language, voices_data)
    # Retorna apenas a lista de opções e o primeiro valor
    if voice_options:
        return gr.Dropdown(choices=voice_options, value=voice_options[0])
    return gr.Dropdown(choices=[], value=None)

def update_voices_and_refresh():
    # Execute get_voices to update the voices.json file
    get_voices()
    # Reload the voices data
    voices_data = load_voices()
    available_languages = list(voices_data.keys())
    # Get initial voices for the first language
    initial_voices = get_voice_options(available_languages[0], voices_data) if available_languages else []
    
    return (
        gr.Dropdown(choices=available_languages, value=available_languages[0] if available_languages else None),
        gr.Dropdown(choices=initial_voices, value=initial_voices[0] if initial_voices else None)
    )

def remove_silence(input_file, output_file):
    audio = AudioSegment.from_wav(input_file)
    
    # Encontra os segmentos de áudio que não são silêncio
    segments = split_on_silence(audio, min_silence_len=500, silence_thresh=-40)
    
    # Concatena os segmentos de áudio não silenciosos
    non_silent_audio = AudioSegment.silent(duration=0)
    for segment in segments:
        non_silent_audio += segment
    
    # Salva o áudio sem as partes de silêncio
    non_silent_audio.export(output_file, format="wav")

def controlador_generate_audio(audio_input, voice_model_input, speed_input, pitch_input, volume_input, checkbox_cortar_silencio):
    # Gerar áudio
    audio_file = generate_audio(audio_input, voice_model_input, speed_input, pitch_input, volume_input)
    if audio_file:
        print("Áudio gerado com sucesso:", audio_file)
        # Verificar se o checkbox de cortar silêncio está marcado
        if checkbox_cortar_silencio:
            print("Cortando silêncio...")
            # Remover silêncio do áudio
            remove_silence(audio_file, audio_file)
            print("Silêncio removido com sucesso!")
    else:
        print("Erro ao gerar áudio.")
    return audio_file  # Retornar o caminho do arquivo de áudio

def generate_audio(texto, modelo_de_voz, velocidade, tom, volume):
    # Extract actual voice name from formatted string if necessary
    actual_voice = extract_voice_name(modelo_de_voz)
    
    # Format parameters with proper signs
    if velocidade >= 0:
        rate_str = f"+{velocidade}%"
    else:
        rate_str = f"{velocidade}%"
        
    if tom >= 0:
        pitch_str = f"+{tom}Hz"
    else:
        pitch_str = f"{tom}Hz"
        
    if volume >= 0:
        volume_str = f"+{volume}%"
    else:
        volume_str = f"{volume}%"
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    mp3_output_file = os.path.join(output_dir, "new_audio.mp3")
    
    cmd = [
        "edge-tts",
        "--rate=" + rate_str,
        "--pitch=" + pitch_str,
        "--volume=" + volume_str,
        "-v", actual_voice,
        "-t", texto,
        "--write-media", mp3_output_file
    ]
    
    print("Gerando áudio...")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("Erro ao gerar áudio:", e)
        return None
        
    print("Áudio gerado com sucesso!")
    wav_output_file = os.path.join(output_dir, "new_audio.wav")
    audio = AudioSegment.from_mp3(mp3_output_file)
    audio.export(wav_output_file, format="wav")
    return wav_output_file

def generate_audio_from_file(file_path, modelo_de_voz, velocidade, tom, volume):
    # Extrai o nome real da voz formatada, se necessário
    actual_voice = extract_voice_name(modelo_de_voz)
    
    # Formatação dos parâmetros com sinais adequados
    rate_str = f"+{velocidade}%" if velocidade >= 0 else f"{velocidade}%"
    pitch_str = f"+{tom}Hz" if tom >= 0 else f"{tom}Hz"
    volume_str = f"+{volume}%" if volume >= 0 else f"{volume}%"
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    mp3_output_file = os.path.join(output_dir, "new_audio.mp3")
    
    # Usar -f FILE para passar o caminho do arquivo de texto
    cmd = [
        "edge-tts",
        "-f", file_path,   # Certificar que o conteúdo do arquivo seja texto puro
        "--rate=" + rate_str,
        "--pitch=" + pitch_str,
        "--volume=" + volume_str,
        "-v", actual_voice,
        "--write-media", mp3_output_file
    ]
    
    print("Gerando áudio do arquivo...")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("Erro ao gerar áudio:", e)
        return None
        
    print("Áudio gerado com sucesso!")
    wav_output_file = os.path.join(output_dir, "new_audio.wav")
    audio = AudioSegment.from_mp3(mp3_output_file)
    audio.export(wav_output_file, format="wav")
    return wav_output_file

def controlador_generate_audio_from_file(file, voice_model_input, speed_input, pitch_input, volume_input, checkbox_cortar_silencio):
    if file is None:
        return None
    
    # Neste caso, o 'file' já é o caminho do arquivo, então não precisa reescrever
    temp_file_path = file  # Caminho do arquivo que você recebe do Gradio
    
    # Gerar o áudio
    audio_file = generate_audio_from_file(temp_file_path, voice_model_input, speed_input, pitch_input, volume_input)
    
    if audio_file:
        print("Áudio gerado com sucesso:", audio_file)
        if checkbox_cortar_silencio:
            print("Cortando silêncio...")
            remove_silence(audio_file, audio_file)
            print("Silêncio removido com sucesso!")
    else:
        print("Erro ao gerar áudio.")
    
    return audio_file

with gr.Blocks(theme=gr.themes.Default(primary_hue="green", secondary_hue="blue"), title="QuickTTS") as iface:
    gr.Markdown(badges)
    gr.Markdown(description)
    
    voices_data = load_voices()
    available_languages = list(voices_data.keys())

    with gr.Tabs():
        with gr.TabItem("Edge-TTS"):
            gr.Markdown("É ilimitado, podendo até mesmo colocar um livro inteiro, mas claro, tem a questão de tempo, quanto maior o texto, mais demorado é, dublagem por SRT talvez um dia eu bote.")
            
            with gr.Row():
                # Language selection dropdown
                language_input = gr.Dropdown(
                    choices=available_languages,
                    label="Idioma",
                    value=available_languages[52] if available_languages else None
                )
                
                # Voice model dropdown (will be updated based on language selection)
                initial_voices = get_voice_options(available_languages[52], voices_data) if available_languages else []
                voice_model_input = gr.Dropdown(
                    choices=initial_voices,
                    label="Modelo de Voz",
                    value=initial_voices[0] if initial_voices else None
                )
            
            # Connect language selection to voice model update
            language_input.change(
                fn=update_voice_options,
                inputs=[language_input],
                outputs=[voice_model_input]
            )
            
            audio_input = gr.Textbox(label="Texto", value='Texto de exemplo!', interactive=True)
            
            with gr.Row():
                with gr.Column():
                    speed_input = gr.Slider(
                        minimum=-200, 
                        maximum=200, 
                        label="Velocidade (%)", 
                        value=0, 
                        interactive=True
                    )
                with gr.Column():
                    pitch_input = gr.Slider(
                        minimum=-100, 
                        maximum=100, 
                        label="Tom (Hz)", 
                        value=0, 
                        interactive=True
                    )
                with gr.Column():
                    volume_input = gr.Slider(
                        minimum=-99, 
                        maximum=100, 
                        label="Volume (%)", 
                        value=0, 
                        interactive=True
                    )
            
            checkbox_cortar_silencio = gr.Checkbox(label="Cortar Silencio", interactive=True)
            audio_output = gr.Audio(label="Resultado", type="filepath", interactive=False)
            
            with gr.Row():
                edgetts_button = gr.Button(value="Falar")
                edgetts_button.click(
                    controlador_generate_audio,
                    inputs=[
                        audio_input, 
                        voice_model_input, 
                        speed_input, 
                        pitch_input,  # New input
                        volume_input,  # New input
                        checkbox_cortar_silencio
                    ],
                    outputs=[audio_output]
                )
                
                clear_button = gr.ClearButton(audio_input, value='Limpar')
            
            # Add update voices button at the top
            update_voices_btn = gr.Button(value="Atualizar Lista de Vozes")
            # Connect update voices button to refresh function
            update_voices_btn.click(
                fn=update_voices_and_refresh,
                inputs=[],
                outputs=[language_input, voice_model_input]
            )
            gr.Markdown("Agradecimentos a rany2 pelo Edge-TTS")
            
        with gr.TabItem("Lote (Arquivo txt)"):
            gr.Markdown("Carregar texto de um arquivo")            
            # Language and voice selection (same as first tab)
            with gr.Row():
                language_input_file = gr.Dropdown(
                    choices=available_languages,
                    label="Idioma",
                    value=available_languages[52] if available_languages else None
                )
                
                initial_voices = get_voice_options(available_languages[52], voices_data) if available_languages else []
                voice_model_input_file = gr.Dropdown(
                    choices=initial_voices,
                    label="Modelo de Voz",
                    value=initial_voices[0] if initial_voices else None
                )
            
            language_input_file.change(
                fn=update_voice_options,
                inputs=[language_input_file],
                outputs=[voice_model_input_file]
            )
            gr.Markdown("O programa vai ler linha por linha e entregar em um único áudio")      
            # File input
            file_input = gr.File(
                label="Arquivo de Texto",
                file_types=[".txt"],
                type="filepath"
            )
            
            with gr.Row():
                with gr.Column():
                    speed_input_file = gr.Slider(
                        minimum=-200, 
                        maximum=200, 
                        label="Velocidade (%)", 
                        value=0, 
                        interactive=True
                    )
                with gr.Column():
                    pitch_input_file = gr.Slider(
                        minimum=-100, 
                        maximum=100, 
                        label="Tom (Hz)", 
                        value=0, 
                        interactive=True
                    )
                with gr.Column():
                    volume_input_file = gr.Slider(
                        minimum=-99, 
                        maximum=100, 
                        label="Volume (%)", 
                        value=0, 
                        interactive=True
                    )
            
            checkbox_cortar_silencio_file = gr.Checkbox(label="Cortar Silencio", interactive=True)
            audio_output_file = gr.Audio(label="Resultado", type="filepath", interactive=False)
            with gr.Row():
                edgetts_button_file = gr.Button(value="Falar")
                edgetts_button_file.click(
                    controlador_generate_audio_from_file,
                    inputs=[
                        file_input,
                        voice_model_input_file,
                        speed_input_file,
                        pitch_input_file,
                        volume_input_file,
                        checkbox_cortar_silencio_file
                    ],
                    outputs=[audio_output_file]
                )
                
                clear_button_file = gr.ClearButton(file_input, value='Limpar')
            
            gr.Markdown("Agradecimentos a rany2 pelo Edge-TTS")
            
        gr.Markdown("""
                    Desenvolvido por Rafael Godoy <br>
                    Apoie o projeto pelo https://nubank.com.br/pagar/1ls6a4/0QpSSbWBSq, qualquer valor é bem vindo.
                    """)
    iface.launch()