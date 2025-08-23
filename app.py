# app.py

import gradio as gr
from get_voices import get_voices
from header import badges, description
import os
from pathlib import Path

# --- Imports from our new modules ---
from utils import listar_audios, tocar_audio
from edgeTTS import (
    load_voices, get_voice_options, controlador_generate_audio,
    controlador_generate_audio_from_file, controlador_process_srt_file
)
from tiktokTTS import (
    TIKTOK_TTS_AVAILABLE, TIKTOK_VOICES_CATEGORIZED, get_tiktok_voice_options, 
    controlador_generate_audio_tiktok, controlador_process_srt_file_tiktok
)

# --- Global Settings ---
srt_temp_deleta = True 

def load_samples(sample_dir="samples"):
    """
    Escaneia um diretório por pares de arquivos (.srt, .mp3) e os formata
    para o componente gr.Examples.
    """
    samples_path = Path(sample_dir)
    if not samples_path.exists():
        print(f"Aviso: Diretório de exemplos '{sample_dir}' não encontrado.")
        return []

    examples = []
    # Itera sobre todos os arquivos .srt no diretório
    for srt_file in sorted(samples_path.glob("*.srt")):
        mp3_file = srt_file.with_suffix(".mp3")
        # Verifica se o arquivo .mp3 correspondente existe
        if mp3_file.exists():
            # Adiciona o par [caminho_srt, caminho_mp3] à lista
            examples.append([str(srt_file), str(mp3_file)])
    
    if not examples:
        print(f"Aviso: Nenhum par de exemplos (.srt, .mp3) encontrado em '{sample_dir}'.")

    return examples
    
# --- UI Helper Functions ---
def update_edge_voice_options(language, voices_data):
    voice_options = get_voice_options(language, voices_data)
    if voice_options:
        return gr.update(choices=voice_options, value=voice_options[0], interactive=True)
    return gr.update(choices=[], value=None, interactive=False)

def update_tiktok_voice_options(language):
    voices = get_tiktok_voice_options(language)
    return gr.update(choices=voices, value=voices[0] if voices else None)

def update_voices_and_refresh():
    print("Iniciando a atualização da lista de vozes...")
    get_voices()
    voices_data = load_voices()
    available_languages = list(voices_data.keys())
    initial_voices = get_voice_options(available_languages[0], voices_data) if available_languages else []
    return (
        gr.update(choices=available_languages, value=available_languages[0] if available_languages else None),
        gr.update(choices=initial_voices, value=initial_voices[0] if initial_voices else None)
    )

# --- Gradio Interface ---
with gr.Blocks(theme=gr.themes.Default(primary_hue="green", secondary_hue="blue"), title="QuickTTS") as iface:
    gr.Markdown(badges)
    gr.Markdown(description)
    
    edge_voices_data = load_voices()
    edge_available_languages = list(edge_voices_data.keys())
    tiktok_available_categories = list(TIKTOK_VOICES_CATEGORIZED.keys())

    with gr.Tabs():
        with gr.TabItem("TTS"):
            gr.Markdown("Gere áudio a partir de texto usando diferentes provedores.")
            provider_choice = gr.Radio(choices=["Edge-TTS", "TikTok"], value="Edge-TTS", label="Escolha o Provedor de TTS", interactive=TIKTOK_TTS_AVAILABLE)
            
            with gr.Column(visible=True) as edge_tts_ui:
                with gr.Row():
                    lang_val = edge_available_languages[52] if len(edge_available_languages) > 52 else None
                    language_input = gr.Dropdown(choices=edge_available_languages, label="Idioma", value=lang_val)
                    initial_voices = get_voice_options(lang_val, edge_voices_data) if lang_val else []
                    voice_model_input = gr.Dropdown(choices=initial_voices, label="Modelo de Voz", value=initial_voices[0] if initial_voices else None)
                audio_input = gr.Textbox(label="Texto", value='Texto de exemplo!', interactive=True)
                with gr.Row():
                    speed_input = gr.Slider(-200, 200, label="Velocidade (%)", value=0, interactive=True)
                    pitch_input = gr.Slider(-100, 100, label="Tom (Hz)", value=0, interactive=True)
                    volume_input = gr.Slider(-99, 100, label="Volume (%)", value=0, interactive=True)
                checkbox_cortar_silencio = gr.Checkbox(label="Cortar Silencio", interactive=True)

            with gr.Column(visible=False) as tiktok_tts_ui:
                gr.Markdown("Use as vozes populares do TikTok.")
                with gr.Row():
                    tiktok_category_input = gr.Dropdown(choices=tiktok_available_categories, label="Idioma / Categoria", value=tiktok_available_categories[0])
                    initial_tiktok_voices = get_tiktok_voice_options(tiktok_available_categories[0])
                    tiktok_voice_model_input = gr.Dropdown(choices=initial_tiktok_voices, label="Modelo de Voz", value=initial_tiktok_voices[0] if initial_tiktok_voices else None)
                tiktok_audio_input = gr.Textbox(label="Texto", value='Olá, isso é um teste com a voz do TikTok!', interactive=True)
                # ADICIONADO: Checkbox para o TikTok
                checkbox_cortar_silencio_tiktok = gr.Checkbox(label="Cortar Silencio", interactive=True)

            audio_output = gr.Audio(label="Resultado", type="filepath", interactive=False, show_download_button=True)
            with gr.Row():
                gerar_button = gr.Button(value="Falar")
                clear_button = gr.ClearButton(components=[audio_input, tiktok_audio_input], value='Limpar Texto')

            update_voices_btn = gr.Button(value="Atualizar Lista de Vozes (Edge-TTS)")

            # --- Event Handlers for TTS Tab ---
            language_input.change(fn=lambda lang: update_edge_voice_options(lang, edge_voices_data), inputs=language_input, outputs=voice_model_input)
            tiktok_category_input.change(fn=update_tiktok_voice_options, inputs=tiktok_category_input, outputs=tiktok_voice_model_input)
            update_voices_btn.click(fn=update_voices_and_refresh, inputs=[], outputs=[language_input, voice_model_input])
            
            def switch_provider_ui(provider):
                return gr.update(visible=provider == "Edge-TTS"), gr.update(visible=provider == "TikTok")
            provider_choice.change(fn=switch_provider_ui, inputs=provider_choice, outputs=[edge_tts_ui, tiktok_tts_ui])

            # MODIFICADO: Função principal agora aceita o novo checkbox
            def gerar_audio_principal(provider, edge_text, edge_voice, speed, pitch, vol, cut_silence, tiktok_voice, tiktok_text, tiktok_cut_silence):
                if provider == "Edge-TTS":
                    return controlador_generate_audio(edge_text, edge_voice, speed, pitch, vol, cut_silence)
                else:
                    return controlador_generate_audio_tiktok(tiktok_voice, tiktok_text, None, tiktok_cut_silence)
            
            # MODIFICADO: Lista de inputs do botão foi atualizada
            gerar_button.click(
                fn=gerar_audio_principal, 
                inputs=[
                    provider_choice, audio_input, voice_model_input, speed_input, pitch_input, volume_input, checkbox_cortar_silencio, 
                    tiktok_voice_model_input, tiktok_audio_input, checkbox_cortar_silencio_tiktok
                ], 
                outputs=audio_output
            )

        with gr.TabItem("Lote (Arquivo txt)"):
            provider_choice_file = gr.Radio(choices=["Edge-TTS", "TikTok"], value="Edge-TTS", label="Escolha o Provedor de TTS", interactive=TIKTOK_TTS_AVAILABLE)
            file_input = gr.File(label="Arquivo de Texto", file_types=[".txt"], type="filepath")
            
            with gr.Column(visible=True) as edge_tts_ui_file:
                 with gr.Row():
                    lang_val_file = edge_available_languages[52] if len(edge_available_languages) > 52 else None
                    language_input_file = gr.Dropdown(choices=edge_available_languages, label="Idioma", value=lang_val_file)
                    initial_voices_file = get_voice_options(lang_val_file, edge_voices_data) if lang_val_file else []
                    voice_model_input_file = gr.Dropdown(choices=initial_voices_file, label="Modelo de Voz", value=initial_voices_file[0] if initial_voices_file else None)
                 with gr.Row():
                    speed_input_file = gr.Slider(-200, 200, label="Velocidade (%)", value=0, interactive=True)
                    pitch_input_file = gr.Slider(-100, 100, label="Tom (Hz)", value=0, interactive=True)
                    volume_input_file = gr.Slider(-99, 100, label="Volume (%)", value=0, interactive=True)
                 checkbox_cortar_silencio_file = gr.Checkbox(label="Cortar Silencio", interactive=True)

            with gr.Column(visible=False) as tiktok_tts_ui_file:
                with gr.Row():
                    tiktok_category_input_file = gr.Dropdown(choices=tiktok_available_categories, label="Idioma / Categoria", value=tiktok_available_categories[0])
                    initial_tiktok_voices_file = get_tiktok_voice_options(tiktok_available_categories[0])
                    tiktok_voice_model_input_file = gr.Dropdown(choices=initial_tiktok_voices_file, label="Modelo de Voz", value=initial_tiktok_voices_file[0] if initial_tiktok_voices_file else None)
                # ADICIONADO: Checkbox para o TikTok em lote
                checkbox_cortar_silencio_tiktok_file = gr.Checkbox(label="Cortar Silencio", interactive=True)

            audio_output_file = gr.Audio(label="Resultado", type="filepath", interactive=False, show_download_button=True)
            with gr.Row():
                gerar_button_file = gr.Button(value="Falar")
                clear_button_file = gr.ClearButton(file_input, value='Limpar')

            # --- Event Handlers for Lote Tab ---
            language_input_file.change(fn=lambda lang: update_edge_voice_options(lang, edge_voices_data), inputs=language_input_file, outputs=voice_model_input_file)
            tiktok_category_input_file.change(fn=update_tiktok_voice_options, inputs=tiktok_category_input_file, outputs=tiktok_voice_model_input_file)
            provider_choice_file.change(fn=switch_provider_ui, inputs=provider_choice_file, outputs=[edge_tts_ui_file, tiktok_tts_ui_file])
            
            # MODIFICADO: Função principal agora aceita o novo checkbox
            def gerar_audio_lote_principal(provider, file, edge_voice, speed, pitch, vol, cut_silence, tiktok_voice, tiktok_cut_silence):
                if provider == "Edge-TTS":
                    return controlador_generate_audio_from_file(file, edge_voice, speed, pitch, vol, cut_silence)
                else:
                    return controlador_generate_audio_tiktok(tiktok_voice, None, file, tiktok_cut_silence)
            
            # MODIFICADO: Lista de inputs do botão foi atualizada
            gerar_button_file.click(
                fn=gerar_audio_lote_principal, 
                inputs=[
                    provider_choice_file, file_input, voice_model_input_file, speed_input_file, pitch_input_file, volume_input_file, checkbox_cortar_silencio_file, 
                    tiktok_voice_model_input_file, checkbox_cortar_silencio_tiktok_file
                ], 
                outputs=audio_output_file
            )

        with gr.TabItem("Ler .SRT"):
            gr.Markdown("Gere áudio sincronizado a partir de um arquivo .SRT usando o provedor de sua escolha.")
            
            with gr.Tabs():
                with gr.TabItem("Gerar áudio"):
                    # ADICIONADO: Seletor de provedor para SRT
                    provider_choice_srt = gr.Radio(choices=["Edge-TTS", "TikTok"], value="Edge-TTS", label="Escolha o Provedor de TTS", interactive=TIKTOK_TTS_AVAILABLE)

                    # --- UI do Edge-TTS para SRT ---
                    with gr.Column(visible=True) as edge_tts_ui_srt:
                        gr.Markdown("A velocidade é ajustada automaticamente para cada legenda.")
                        with gr.Row():
                            lang_val_srt = edge_available_languages[52] if len(edge_available_languages) > 52 else None
                            language_input_srt = gr.Dropdown(choices=edge_available_languages, label="Idioma", value=lang_val_srt)
                            initial_voices_srt = get_voice_options(lang_val_srt, edge_voices_data) if lang_val_srt else []
                            voice_model_input_srt = gr.Dropdown(choices=initial_voices_srt, label="Modelo de Voz", value=initial_voices_srt[0] if initial_voices_srt else None)
                        with gr.Row():
                            pitch_input_srt = gr.Slider(-100, 100, label="Tom (Hz)", value=0, interactive=True)
                            volume_input_srt = gr.Slider(-99, 200, label="Volume (%)", value=0, interactive=True)

                    # --- UI do TikTok para SRT ---
                    with gr.Column(visible=False) as tiktok_tts_ui_srt:
                        gr.Markdown("A velocidade do áudio será ajustada automaticamente para cada legenda. Tom e volume não são aplicáveis.")
                        with gr.Row():
                            tiktok_category_input_srt = gr.Dropdown(choices=tiktok_available_categories, label="Idioma / Categoria", value=tiktok_available_categories[0])
                            initial_tiktok_voices_srt = get_tiktok_voice_options(tiktok_available_categories[0])
                            tiktok_voice_model_input_srt = gr.Dropdown(choices=initial_tiktok_voices_srt, label="Modelo de Voz", value=initial_tiktok_voices_srt[0] if initial_tiktok_voices_srt else None)

                    # --- Componentes Comuns ---
                    srt_input = gr.File(label="Arquivo SRT", file_types=[".srt"], type="filepath")
                    audio_output_srt = gr.Audio(label="Resultado", type="filepath", interactive=False, show_download_button=True)
                    progress_bar_srt = gr.Progress(track_tqdm=True)
                    # --- ADICIONADO: Componente de Exemplos ---
                    gr.Examples(
                        examples=load_samples(),
                        inputs=[srt_input, audio_output_srt],
                        outputs=[srt_input, audio_output_srt],
                        label="Exemplos (Clique para carregar)",
                        # A função fn=lambda x,y: (x,y) é um truque para carregar os dados diretamente
                        fn=lambda srt_path, audio_path: (srt_path, audio_path) 
                    )
                    audio_list_target = gr.Dropdown(visible=False)
                    with gr.Row():
                        srt_button = gr.Button(value="Gerar Áudio")
                        clear_button_srt = gr.ClearButton(srt_input, value='Limpar')
                    
                    # --- Lógica e Event Handlers ---
                    def switch_provider_ui_srt(provider):
                        return gr.update(visible=provider == "Edge-TTS"), gr.update(visible=provider == "TikTok")
                    
                    provider_choice_srt.change(fn=switch_provider_ui_srt, inputs=provider_choice_srt, outputs=[edge_tts_ui_srt, tiktok_tts_ui_srt])
                    language_input_srt.change(fn=lambda lang: update_edge_voice_options(lang, edge_voices_data), inputs=language_input_srt, outputs=voice_model_input_srt)
                    tiktok_category_input_srt.change(fn=update_tiktok_voice_options, inputs=tiktok_category_input_srt, outputs=tiktok_voice_model_input_srt)

                    def controlador_srt_principal(provider, srt_file, edge_voice, pitch, volume, tiktok_voice, progress=gr.Progress(track_tqdm=True)):
                        """
                        Função roteadora que recebe o rastreador de progresso do Gradio
                        e o passa para os controladores específicos do provedor.
                        """
                        if provider == "Edge-TTS":
                            audio_file = controlador_process_srt_file(srt_file, edge_voice, pitch, volume, srt_temp_deleta, progress=progress)
                        else: # TikTok
                            audio_file = controlador_process_srt_file_tiktok(srt_file, tiktok_voice, srt_temp_deleta, progress=progress)
                        
                        return audio_file, gr.update(choices=listar_audios())
                    
                    # MODIFICADO: A chamada de clique permanece a mesma, o Gradio injeta o `progress` automaticamente
                    srt_button.click(
                        fn=controlador_srt_principal, 
                        inputs=[provider_choice_srt, srt_input, voice_model_input_srt, pitch_input_srt, volume_input_srt, tiktok_voice_model_input_srt], 
                        outputs=[audio_output_srt, audio_list_target], 
                        queue=True
                    )

                with gr.TabItem("Arquivos gerados"):
                    audio_list = gr.Dropdown(label="Arquivos de áudio", choices=listar_audios(), interactive=True)
                    audio_list_target.change(lambda x: x, inputs=[audio_list_target], outputs=[audio_list])
                    play_button = gr.Button(value="Tocar")
                    refresh_button = gr.Button(value="Atualizar Lista")
                    audio_player = gr.Audio(label="Reproduzir", type="filepath", interactive=False, show_download_button=True)
                    status_message = gr.Textbox(label="Status", interactive=False, visible=True)
                    
                    def update_audio_list():
                        arquivos = listar_audios()
                        return gr.update(choices=arquivos, value=None), "Lista atualizada."
                    
                    refresh_button.click(fn=update_audio_list, outputs=[audio_list, status_message], queue=True)
                    play_button.click(fn=tocar_audio, inputs=[audio_list], outputs=[audio_player], queue=True)
        gr.Markdown("""
        <hr>
        <div style='text-align: center; font-size: 0.9em; color: #777;'>
            <p>
                <strong>Desenvolvido por Rafael Godoy</strong>
                <br>
                Apoie o projeto, qualquer valor é bem-vindo: 
                <a href='https://nubank.com.br/pagar/1ls6a4/0QpSSbWBSq' target='_blank'><strong>Apoiar via PIX</strong></a>
            </p>
            <p style='margin-top: 10px;'>
                Este aplicativo utiliza as fantásticas bibliotecas de código aberto:
                <br>
                <a href='https://github.com/rany2/edge-tts' target='_blank'>edge-tts</a> de rany2
                &bull;
                <a href='https://github.com/mark-rez/TikTok-Voice-TTS' target='_blank'>TikTok-Voice-TTS</a> de mark-rez
            </p>
        </div>
        """)
    iface.launch()