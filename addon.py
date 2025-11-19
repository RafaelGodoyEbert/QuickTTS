# /addons/edge_tts_addon/addon.py

import gradio as gr
# Importa a lógica original do seu arquivo
from . import edgeTTS 

# --- Metadados do Addon ---
def get_name():
    """Retorna o nome de exibição do addon."""
    return "Edge-TTS"

# --- Funções de UI do Addon ---
def create_ui():
    """Cria e retorna os componentes da UI do Gradio para este addon."""
    edge_voices_data = edgeTTS.load_voices()
    edge_available_languages = list(edge_voices_data.keys())
    
    with gr.Column() as ui_block:
        with gr.Row():
            lang_val = edge_available_languages[52] if len(edge_available_languages) > 52 else None
            language_input = gr.Dropdown(choices=edge_available_languages, label="Idioma", value=lang_val, elem_id="edge_language")
            initial_voices = edgeTTS.get_voice_options(lang_val, edge_voices_data) if lang_val else []
            voice_model_input = gr.Dropdown(choices=initial_voices, label="Modelo de Voz", value=initial_voices[0] if initial_voices else None, elem_id="edge_voice")
        
        audio_input = gr.Textbox(label="Texto", value='Texto de exemplo!', interactive=True, elem_id="edge_text")
        
        with gr.Row():
            speed_input = gr.Slider(-200, 200, label="Velocidade (%)", value=0, interactive=True, elem_id="edge_speed")
            pitch_input = gr.Slider(-100, 100, label="Tom (Hz)", value=0, interactive=True, elem_id="edge_pitch")
            volume_input = gr.Slider(-99, 100, label="Volume (%)", value=100, interactive=True, elem_id="edge_volume")
        
        cut_silence_checkbox = gr.Checkbox(label="Cortar Silencio", interactive=True, elem_id="edge_cut_silence")

        # Event handler para a UI interna do addon
        language_input.change(
            fn=lambda lang: edgeTTS.update_edge_voice_options(lang, edge_voices_data), 
            inputs=language_input, 
            outputs=voice_model_input
        )
    
    # Retorna o bloco da UI e uma lista de todos os inputs que a função de geração precisará
    inputs = [audio_input, voice_model_input, speed_input, pitch_input, volume_input, cut_silence_checkbox]
    return ui_block, inputs

# --- Funções de Geração de Áudio ---
def generate_audio(text, voice_model, speed, pitch, volume, cut_silence):
    """Função principal que gera o áudio."""
    return edgeTTS.controlador_generate_audio(text, voice_model, speed, pitch, volume, cut_silence)

def process_srt(srt_file, voice_model, pitch, volume, srt_temp_deleta):
    """Função para processar arquivos SRT."""
    return edgeTTS.controlador_process_srt_file(srt_file, voice_model, pitch, volume, srt_temp_deleta)