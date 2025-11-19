# /addons/tiktok-tts-addon/addon.py (VERSÃO FINAL COM LÓGICA DE SRT CORRIGIDA E ROBUSTA)

import gradio as gr
import sys
from pathlib import Path
import asyncio
import pysrt
from tqdm import tqdm
import shutil
import os

# --- Bloco de Importação ---
addon_dir = Path(__file__).parent.resolve()
if str(addon_dir) not in sys.path:
    sys.path.insert(0, str(addon_dir))
try:
    from TikTok_TTS.tiktok_voice import Voice, tts
except ImportError as e:
    raise ImportError(f"Falha ao importar a biblioteca TikTok. Verifique a estrutura de pastas. Erro: {e}")

# --- Função de Inicialização ---
def initialize(root_path):
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))

# --- Lógica do Controlador ---

def controlador_generate_audio_tiktok(voice_str, text=None, file_path=None, cut_silence=False):
    if not text and not file_path: raise gr.Error("Texto ou arquivo não fornecido.")
    output_dir = "output"; Path(output_dir).mkdir(exist_ok=True)
    output_file = Path(output_dir) / "tiktok_audio.mp3"
    input_text = text
    if file_path:
        with open(file_path.name, 'r', encoding='utf-8') as f:
            input_text = f.read()
    try:
        tts(input_text, Voice[voice_str], str(output_file))
        if cut_silence:
            from utils_file import remove_silence
            remove_silence(str(output_file), str(output_file))
        return str(output_file)
    except Exception as e:
        raise gr.Error(f"Ocorreu um erro no TikTok TTS: {e}")

# --- LÓGICA DE SRT REESTRUTURADA PARA SEGUIR O PADRÃO EDGETTS ---

async def process_srt_file_tiktok_async(srt_file_path, voice_str, output_dir_str, srt_temp_deleta, progress=None):
    from utils_file import timetoms, merge_audio_files, adjust_audio_speed
    from pydub import AudioSegment

    subs = pysrt.open(srt_file_path)
    output_dir = Path(output_dir_str)
    output_dir.mkdir(parents=True, exist_ok=True)
    max_retries = 3

    for sub in tqdm(subs, desc="Gerando e Ajustando Áudios com TikTok"):
        final_segment_file = output_dir / f"{sub.index:02d}.mp3"
        temp_tts_file = output_dir / f"{sub.index:02d}_temp.mp3"
        target_duration_ms = timetoms(sub.end) - timetoms(sub.start)

        if final_segment_file.exists() and final_segment_file.stat().st_size > 1024:
            continue

        success = False
        for attempt in range(max_retries):
            try:
                # ETAPA 1: Gerar o áudio com a duração natural
                await asyncio.to_thread(tts, sub.text, Voice[voice_str], str(temp_tts_file))

                if temp_tts_file.exists() and temp_tts_file.stat().st_size > 1024:
                    # ETAPA 2 (CRUCIAL): Ajustar a velocidade do áudio gerado para corresponder à legenda
                    await adjust_audio_speed(str(temp_tts_file), str(final_segment_file), target_duration_ms)
                    
                    # ETAPA 3: Limpar o arquivo temporário
                    os.remove(temp_tts_file)
                    
                    success = True
                    break
                else:
                    print(f"Aviso: Tentativa {attempt + 1} (TikTok) gerou um arquivo temporário inválido. Retentando...")
            
            except Exception as e:
                print(f"Aviso: Tentativa {attempt + 1} (TikTok) falhou com erro: {e}. Retentando...")
                # Limpa o arquivo temporário em caso de falha para a próxima tentativa
                if temp_tts_file.exists():
                    os.remove(temp_tts_file)

        if not success:
            print(f"ERRO: Todas as tentativas (TikTok) falharam para o índice {sub.index}. Gerando silêncio.")
            silent_segment = AudioSegment.silent(duration=target_duration_ms)
            silent_segment.export(str(final_segment_file), format="mp3")

    print("Todos os segmentos foram processados. Mesclando áudios...")
    final_audio = await merge_audio_files(output_dir, srt_file_path)
    
    if srt_temp_deleta:
        shutil.rmtree(output_dir, ignore_errors=True)
        print(f"Pasta temporária {output_dir} apagada.")
        
    return final_audio

def controlador_process_srt_file_tiktok(srt_file, voice_str, srt_temp_deleta, progress=None):
    if not srt_file: return None
    srt_filename_stem = Path(srt_file.name).stem
    output_dir = f"output/srt_temp_{srt_filename_stem}"
    try:
        return asyncio.run(process_srt_file_tiktok_async(srt_file.name, voice_str, output_dir, srt_temp_deleta, progress=progress))
    except Exception as e:
        raise gr.Error(f"Ocorreu um erro no processamento SRT do TikTok: {e}")

# --- Contrato do Addon ---

TIKTOK_VOICES_CATEGORIZED = {
    'Português (Brasil)': ['BR_FEMALE_1', 'BR_FEMALE_2', 'BR_FEMALE_3', 'BR_MALE', 'BP_FEMALE_IVETE', 'BP_FEMALE_LUDMILLA', 'PT_FEMALE_LHAYS', 'PT_FEMALE_LAIZZA', 'PT_MALE_BUENO'],
    'Inglês (EUA)': ['US_FEMALE_1', 'US_FEMALE_2', 'US_MALE_1', 'US_MALE_2', 'US_MALE_3', 'US_MALE_4'],
}
def get_tiktok_voice_options(language):
    return TIKTOK_VOICES_CATEGORIZED.get(language, [])

def get_name(): return "TikTok-TTS"

def create_ui():
    available_categories = list(TIKTOK_VOICES_CATEGORIZED.keys())
    default_category = 'Português (Brasil)'
    with gr.Column() as ui_block:
        gr.Markdown("Use as vozes populares do TikTok.")
        with gr.Row():
            category_input = gr.Dropdown(choices=available_categories, label="Idioma", value=default_category)
            initial_voices = get_tiktok_voice_options(default_category)
            voice_model_input = gr.Dropdown(choices=initial_voices, label="Voz", value=initial_voices[0] if initial_voices else None)
        audio_input = gr.Textbox(label="Texto", value='Teste de áudio com TikTok.', interactive=True)
        cut_silence_checkbox = gr.Checkbox(label="Cortar Silencio", interactive=True)
        def update_voice_list(category):
            voices = get_tiktok_voice_options(category)
            return gr.update(choices=voices, value=voices[0] if voices else None)
        category_input.change(fn=update_voice_list, inputs=category_input, outputs=voice_model_input)
    inputs = [audio_input, voice_model_input, cut_silence_checkbox]
    return ui_block, inputs

def generate_audio(text, voice_model, cut_silence):
    if not voice_model: raise gr.Error("Nenhuma voz do TikTok selecionada.")
    return controlador_generate_audio_tiktok(voice_model, text, None, cut_silence)

def create_lote_ui():
    available_categories = list(TIKTOK_VOICES_CATEGORIZED.keys())
    default_category = 'Português (Brasil)'
    with gr.Column() as ui_block:
        with gr.Row():
            category_input_file = gr.Dropdown(choices=available_categories, label="Idioma", value=default_category)
            initial_voices_file = get_tiktok_voice_options(default_category)
            voice_model_input_file = gr.Dropdown(choices=initial_voices_file, label="Voz", value=initial_voices_file[0] if initial_voices_file else None)
        checkbox_cortar_silencio_file = gr.Checkbox(label="Cortar Silencio", interactive=True)
        def update_voice_list_lote(category):
            voices = get_tiktok_voice_options(category)
            return gr.update(choices=voices, value=voices[0] if voices else None)
        category_input_file.change(fn=update_voice_list_lote, inputs=category_input_file, outputs=voice_model_input_file)
    inputs = [voice_model_input_file, checkbox_cortar_silencio_file]
    return ui_block, inputs

def process_lote(file_obj, voice_model, cut_silence):
    if not file_obj: raise gr.Error("Nenhum arquivo .txt enviado.")
    if not voice_model: raise gr.Error("Nenhuma voz do TikTok selecionada.")
    return controlador_generate_audio_tiktok(voice_model, None, file_obj, cut_silence)

def create_srt_ui():
    available_categories = list(TIKTOK_VOICES_CATEGORIZED.keys())
    default_category = 'Português (Brasil)'
    with gr.Column() as ui_block:
        gr.Markdown("A velocidade do áudio será ajustada para corresponder à duração da legenda.")
        with gr.Row():
            category_input_srt = gr.Dropdown(choices=available_categories, label="Idioma / Categoria", value=default_category)
            initial_voices_srt = get_tiktok_voice_options(default_category)
            voice_model_input_srt = gr.Dropdown(choices=initial_voices_srt, label="Voz", value=initial_voices_srt[0] if initial_voices_srt else None)
        checkbox_deletar_temp_srt = gr.Checkbox(label="Apagar arquivos temporários após a conclusão", value=True, interactive=True)
        def update_voice_list_srt(category):
            voices = get_tiktok_voice_options(category)
            return gr.update(choices=voices, value=voices[0] if voices else None)
        category_input_srt.change(fn=update_voice_list_srt, inputs=category_input_srt, outputs=voice_model_input_srt)
    inputs = [voice_model_input_srt, checkbox_deletar_temp_srt]
    return ui_block, inputs

def process_srt(file_obj, voice_model, srt_temp_deleta):
    if not file_obj: raise gr.Error("Nenhum arquivo .srt enviado.")
    if not voice_model: raise gr.Error("Nenhuma voz do TikTok selecionada.")
    return controlador_process_srt_file_tiktok(file_obj, voice_model, srt_temp_deleta)