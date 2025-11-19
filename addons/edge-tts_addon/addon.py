# /addons/edge_tts_addon/addon.py (VERSÃO CORRIGIDA)

import gradio as gr
import sys
from pathlib import Path

# --- Função de Inicialização ---
def initialize(root_path):
    """Permite que o app.py informe ao addon onde fica o diretório raiz do projeto."""
    # Adiciona o diretório raiz ao path para que possamos encontrar 'utils_file.py'
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))

# --- Bloco de Importação Dinâmica ---
# Adiciona o próprio diretório do addon ao path para encontrar 'edgeTTS.py'
addon_dir = Path(__file__).parent.resolve()
if str(addon_dir) not in sys.path:
    sys.path.insert(0, str(addon_dir))
try:
    import edgeTTS
    # utils_file será importado com sucesso após a chamada de initialize()
except ImportError as e:
    raise ImportError(f"Falha na importação inicial. Verifique se 'edgeTTS.py' está em '{addon_dir}'. Erro: {e}")
# --- Fim do Bloco de Importação ---

# Carrega os dados das vozes uma vez para serem usados por todas as funções de UI
voices_data = edgeTTS.load_voices()
available_languages = list(voices_data.keys())
default_lang = 'Portuguese' if 'Portuguese' in available_languages else available_languages[0] if available_languages else None

def get_name():
    return "Edge-TTS"

# (O resto do arquivo é o mesmo da resposta anterior, apenas a parte de importação foi corrigida)
# --- Contrato da Aba Principal (TTS) ---
def create_ui():
    with gr.Column() as ui_block:
        gr.Markdown("Use as vozes do serviço Text-to-Speech do Microsoft Edge.")
        with gr.Row():
            language_input = gr.Dropdown(choices=available_languages, label="Idioma", value=default_lang)
            initial_voices = edgeTTS.get_voice_options(default_lang, voices_data)
            voice_model_input = gr.Dropdown(choices=initial_voices, label="Modelo de Voz", value=initial_voices[0] if initial_voices else None)
        audio_input = gr.Textbox(label="Texto", value='Olá, mundo!', interactive=True)
        with gr.Row():
            speed_input = gr.Slider(-200, 200, label="Velocidade (%)", value=0, interactive=True)
            pitch_input = gr.Slider(-100, 100, label="Tom (Hz)", value=0, interactive=True)
            volume_input = gr.Slider(-99, 100, label="Volume (%)", value=100, interactive=True)
        cut_silence_checkbox = gr.Checkbox(label="Cortar Silencio", interactive=True)
        def update_voice_list(language):
            options = edgeTTS.get_voice_options(language, voices_data)
            return gr.update(choices=options, value=options[0] if options else None)
        language_input.change(fn=update_voice_list, inputs=language_input, outputs=voice_model_input)
    inputs = [audio_input, voice_model_input, speed_input, pitch_input, volume_input, cut_silence_checkbox]
    return ui_block, inputs

def generate_audio(text, voice_model, speed, pitch, volume, cut_silence):
    if not voice_model: raise gr.Error("Nenhum modelo de voz selecionado.")
    return edgeTTS.controlador_generate_audio(text, voice_model, speed, pitch, volume, cut_silence)

# --- Contrato da Aba Lote (.txt) ---
def create_lote_ui():
    with gr.Column() as ui_block:
        with gr.Row():
            language_input_file = gr.Dropdown(choices=available_languages, label="Idioma", value=default_lang)
            initial_voices_file = edgeTTS.get_voice_options(default_lang, voices_data)
            voice_model_input_file = gr.Dropdown(choices=initial_voices_file, label="Modelo de Voz", value=initial_voices_file[0] if initial_voices_file else None)
        with gr.Row():
            speed_input_file = gr.Slider(-200, 200, label="Velocidade (%)", value=0, interactive=True)
            pitch_input_file = gr.Slider(-100, 100, label="Tom (Hz)", value=0, interactive=True)
            volume_input_file = gr.Slider(-99, 100, label="Volume (%)", value=100, interactive=True)
        checkbox_cortar_silencio_file = gr.Checkbox(label="Cortar Silencio", interactive=True)
        def update_voice_list_lote(language):
            options = edgeTTS.get_voice_options(language, voices_data)
            return gr.update(choices=options, value=options[0] if options else None)
        language_input_file.change(fn=update_voice_list_lote, inputs=language_input_file, outputs=voice_model_input_file)
    inputs = [voice_model_input_file, speed_input_file, pitch_input_file, volume_input_file, checkbox_cortar_silencio_file]
    return ui_block, inputs

def process_lote(file_obj, voice_model, speed, pitch, volume, cut_silence):
    if not file_obj: raise gr.Error("Nenhum arquivo .txt enviado.")
    if not voice_model: raise gr.Error("Nenhum modelo de voz selecionado.")
    return edgeTTS.controlador_generate_audio_from_file(file_obj, voice_model, speed, pitch, volume, cut_silence)

# --- Contrato da Aba SRT ---
def create_srt_ui():
    with gr.Column() as ui_block:
        gr.Markdown("A velocidade é ajustada automaticamente para cada legenda.")
        with gr.Row():
            language_input_srt = gr.Dropdown(choices=available_languages, label="Idioma", value=default_lang)
            initial_voices_srt = edgeTTS.get_voice_options(default_lang, voices_data)
            voice_model_input_srt = gr.Dropdown(choices=initial_voices_srt, label="Modelo de Voz", value=initial_voices_srt[0] if initial_voices_srt else None)
        with gr.Row():
            pitch_input_srt = gr.Slider(-100, 100, label="Tom (Hz)", value=0, interactive=True)
            volume_input_srt = gr.Slider(-99, 200, label="Volume (%)", value=100, interactive=True)
        checkbox_deletar_temp_srt = gr.Checkbox(label="Apagar arquivos temporários após a conclusão", value=True, interactive=True)
        def update_voice_list_srt(language):
            options = edgeTTS.get_voice_options(language, voices_data)
            return gr.update(choices=options, value=options[0] if options else None)
        language_input_srt.change(fn=update_voice_list_srt, inputs=language_input_srt, outputs=voice_model_input_srt)
    inputs = [voice_model_input_srt, pitch_input_srt, volume_input_srt, checkbox_deletar_temp_srt]
    return ui_block, inputs

def process_srt(file_obj, voice_model, pitch, volume, srt_temp_deleta):
    if not file_obj: raise gr.Error("Nenhum arquivo .srt enviado.")
    if not voice_model: raise gr.Error("Nenhum modelo de voz selecionado.")
    return edgeTTS.controlador_process_srt_file(file_obj, voice_model, pitch, volume, srt_temp_deleta)