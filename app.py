
import subprocess
import os
import gradio as gr
from pydub import AudioSegment
from voice_map import SUPPORTED_VOICES
from header import badges, description
from pydub.silence import split_on_silence

def generate_audio(texto, modelo_de_voz, velocidade):
    if velocidade >= 0:
        rate_str = f"+{velocidade}%"
    else:
        rate_str = f"{velocidade}%"
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)  # Certifique-se de que o diretório de saída exista

    mp3_output_file = os.path.join(output_dir, "new_audio.mp3")

    cmd = ["edge-tts", "--rate=" + rate_str, "-v", modelo_de_voz, "-t", texto, "--write-media", mp3_output_file]

    print("Gerando áudio...")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("Erro ao gerar áudio:", e)
        return None

    print("Áudio gerado com sucesso!")

    # Convertendo o arquivo de MP3 para WAV
    wav_output_file = os.path.join(output_dir, "new_audio.wav")
    audio = AudioSegment.from_mp3(mp3_output_file)
    audio.export(wav_output_file, format="wav")

    return wav_output_file  # Retorna o caminho completo do arquivo de áudio WAV

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

def controlador_generate_audio(audio_input, voice_model_input, speed_input, checkbox_cortar_silencio):
    # Gerar áudio
    audio_file = generate_audio(audio_input, voice_model_input, speed_input)
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

from elevenlabs import voices, generate
import requests

def generate_audio_elevenlabsfree(texto, voice_name):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)  # Certifique-se de que o diretório de saída exista

    try:
        # Pegar o nome abreviado do modelo de voz
        modelo_abreviado = voice_name

        # Gerar áudio usando elevenlabs
        audio = generate(
            text=texto,
            voice=modelo_abreviado,
            model='eleven_multilingual_v2'
        )
        
        # Caminho completo para o arquivo de saída
        output_file_path = os.path.join(output_dir, "new_audio.wav")

        # Escrever os dados do áudio no arquivo WAV
        with open(output_file_path, 'wb') as wf:
            wf.write(audio)

        print("Áudio gerado com sucesso em:", output_file_path)
        return output_file_path
    except Exception as e:
        print("Erro ao gerar áudio:", e)
        return None
    
def elevenlabsAPI(audio_input_elevenlabs_api, voice_model_input,model_elevenlabs_t, stability_elevenlabs, similarity_boost_elevenlabs, style_elevenlabs, use_speaker_boost_elevenlabs, id_voz_input, id_api, output_dir="output"):
    try:
        if not id_api.strip():
            print("API não fornecida.")
            return None

        id_api_value = id_api
        modelos= model_elevenlabs_t

        if id_voz_input.strip():  # Se um ID de voz foi fornecido
            voice_id = id_voz_input
            print(voice_id)
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": id_api
            }
            print(modelos)
            print(stability_elevenlabs)
            print(similarity_boost_elevenlabs)
            print(style_elevenlabs)
            print(use_speaker_boost_elevenlabs)
            data = {
                "text": audio_input_elevenlabs_api,
                "model_id": modelos,
                "voice_settings": {
                    "stability": stability_elevenlabs,
                    "similarity_boost": similarity_boost_elevenlabs,
                    "style": style_elevenlabs, 
                    "use_speaker_boost": use_speaker_boost_elevenlabs,
                }
            }
            print(data)

            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                audio = response.content
            else:
                print("Erro ao gerar áudio:", response.text)
                return None
        else:  # Se nenhum ID de voz foi fornecido, usar o modelo de voz fornecido
            print(modelos)
            print(stability_elevenlabs)
            print(similarity_boost_elevenlabs)
            print(style_elevenlabs)
            print(use_speaker_boost_elevenlabs)
            audio = generate(
                text=audio_input_elevenlabs_api,
                voice=voice_model_input,
                # voice=Voice(
                #     voice_id='EXAVITQu4vr4xnSDxMaL',
                #     name=voice_model_input,
                #     settings=VoiceSettings(stability=stability_elevenlabs, similarity_boost=similarity_boost_elevenlabs, style=style_elevenlabs, use_speaker_boost=use_speaker_boost_elevenlabs)
                # ),
                model=modelos,
                api_key=id_api
            )

        if audio:
            output_file_path = os.path.join(output_dir, "new_audio.wav")
            with open(output_file_path, 'wb') as wf:
                wf.write(audio)
            print("Áudio gerado com sucesso em:", output_file_path)
            return output_file_path
    except Exception as e:
        print("Erro ao gerar áudio:", e)
        return None

all_voices = voices()
with gr.Blocks(theme=gr.themes.Default(primary_hue="green", secondary_hue="blue"), title="TTS Rápido") as iface:
    gr.Markdown(badges)
    gr.Markdown(description)
    title="TTS Rápido"
    description="Digite o texto, escolha o modelo de voz e ajuste a velocidade para gerar um áudio. O áudio resultante pode ser reproduzido diretamente no Gradio."

    with gr.Tabs():
        with gr.TabItem("Edge-TTS"):
            gr.Markdown("Botei todos os idiomas possível, até onde testei, é ilimitado, podendo até mesmo colocar um livro inteiro, mas claro, tem a questão de tempo, quanto maior o texto, mais demorado é.")
            # Defina os elementos de entrada e saída
            audio_input = gr.Textbox(label="Texto", value='Texto de exemplo!', interactive=True)
            voice_model_input = gr.Dropdown(SUPPORTED_VOICES, label="Modelo de Voz", value="pt-BR-AntonioNeural")
            speed_input = gr.Slider(minimum=-200, maximum=200, label="Velocidade (%)", value=0, interactive=True)
            checkbox_cortar_silencio = gr.Checkbox(label="Cortar Silencio", interactive=True)
            audio_output = gr.Audio(label="Resultado", type="filepath", interactive=False)
            edgetts_button = gr.Button(value="Falar")
            edgetts_button.click(controlador_generate_audio, inputs=[audio_input, voice_model_input, speed_input, checkbox_cortar_silencio], outputs=[audio_output])
            #edgetts_button = gr.Button(value="Falar")
            #edgetts_button.click(fn=generate_audio, inputs=[audio_input, voice_model_input, speed_input], outputs=[audio_output])
            clear_button = gr.ClearButton(audio_input, value='Limpar')
            gr.Markdown("Agradecimentos a rany2 pelo Edge-TTS")

        with gr.TabItem("Elevenlabs"):
            with gr.TabItem("Elevenlabs Free"):
                gr.Markdown("Esse é a API gratuita que é disponivel pela própria Elevenlabs, não sei os limites, mas sei que tem, acredito que após 3 requests seguidos já caia, então tenha certeza o texto que vá usar.")
                audio_input = gr.Textbox(label="Texto (Não botei limite de caracteres, mas não sei se tem limite no request)", value='Texto de exemplo!', interactive=True)
                voice_model_input = gr.Dropdown([ voice.name for voice in all_voices], label="Modelo de Voz", value='Adam', interactive=True)
                gr.Markdown("Se estiver usando huggingface e não rodar, vá em logs, que está acima da imagem do github e veja se já não passou o limite de request da API")
                audio_output = gr.Audio(label="Resultado", type="filepath", interactive=False)
                elevenlabs_button = gr.Button(value="Falar")
                elevenlabs_button.click(fn=generate_audio_elevenlabsfree, inputs=[audio_input, voice_model_input], outputs=[audio_output])
                clear_button = gr.ClearButton(audio_input, value='Limpar')
                gr.Markdown("Agradecimentos ao Elevenlabs")
            with gr.TabItem("Elevenlabs com API"):
                gr.Markdown("Versão com API, basicamente mesma coisa que o site, mas por algum motivo as pessoas me pediram")
                audio_input_elevenlabs_api = gr.Textbox(label="Texto (Acho que o limite é 2500 caracteres)", value='Texto de exemplo!', interactive=True)
                with gr.Row():
                    id_api = gr.Textbox(label="Digite sua API (Obrigatório)", interactive=True)
                    voice_model_input = gr.Dropdown([ voice.name for voice in all_voices], label="Modelo de Voz", value="Adam", interactive=True)
                    id_voz_input = gr.Textbox(label="Ou digite o ID da voz", interactive=True)
                gr.Markdown("Abaixo só funciona o Modelo (multilingual_v1,v2,mono), só funciona todas abaixo se tiver com o ID de voz (Por enquanto). <br> <a href='https://api.elevenlabs.io/v1/voices' target='_blank'>Nesse link</a> tem ID de voz, só filtrar por voice_id")
                with gr.Row():
                    model_elevenlabs_t = gr.Dropdown(['eleven_multilingual_v2', 'eleven_multilingual_v1', 'eleven_monolingual_v1'], label="Modelo", value='eleven_multilingual_v2', interactive=True)
                    stability_elevenlabs = gr.Slider(0, 1, step=0.1, label="Establidade", value=0.67, interactive=True)
                    similarity_boost_elevenlabs = gr.Slider(0, 1, step=0.1, label="Claridade + Similaridade", value=0.8, interactive=True)
                    style_elevenlabs = gr.Slider(0, 1, step=0.1, label="Exagero de estilo", value=0.0, interactive=True)
                    use_speaker_boost_elevenlabs = gr.Checkbox(label="Speaker Boost", value=True, interactive=True)
                gr.Markdown("Se estiver usando huggingface e não rodar, vá em logs, que está acima da imagem do github e veja se já não passou o limite de request da API")
                audio_output = gr.Audio(label="Resultado", type="filepath", interactive=False)
                elevenlabs_button = gr.Button(value="Falar")
                elevenlabs_button.click(fn=elevenlabsAPI, inputs=[audio_input_elevenlabs_api, voice_model_input, model_elevenlabs_t, stability_elevenlabs, similarity_boost_elevenlabs, style_elevenlabs, use_speaker_boost_elevenlabs, id_voz_input, id_api], outputs=[audio_output])
                clear_button = gr.ClearButton(audio_input_elevenlabs_api, value='Limpar')
                gr.Markdown("Agradecimentos ao Elevenlabs")
        with gr.TabItem("Conqui-TTS"):
            gr.Markdown("Em DEV - Conqui")
            # Chame a função do arquivo conqui.py para criar os blocos específicos
            # tabs_conqui = conqui.criar_tab_conqui()
            # Adicione os blocos criados ao bloco principal
            # gr.Component(tabs_conqui)
            # Executar o aplicativo Gradio
        gr.Markdown("""
                    Desenvolvido por Rafael Godoy <br>
                    Apoie o projeto pelo https://nubank.com.br/pagar/1ls6a4/0QpSSbWBSq, qualquer valor é bem vindo.
                    """)
        iface.launch()