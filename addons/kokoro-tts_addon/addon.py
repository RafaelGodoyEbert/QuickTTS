# /addons/kokoro_tts_addon/addon.py 

import gradio as gr
import sys
from pathlib import Path
import numpy as np
import soundfile as sf
import pysrt
from pydub import AudioSegment
import shutil
from tqdm import tqdm
from kokoro import KPipeline
import asyncio
import os


def initialize(root_path):
    """Permite que o app.py informe ao addon onde fica o diretório raiz do projeto."""
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))

# --- Dicionários de Vozes e Idiomas ---
LANGUAGES = {
    "🇺🇸 Inglês": "a", "🇫🇷 Francês": "f", "🇮🇳 Indiano": "h", "🇮🇹 Italiano": "i",
    "🇧🇷 Português Brasileiro": "p", "🇪🇸 Espanhol": "e", "🇬🇧 Inglês Britânico": "b",
    "🇯🇵 Japonês": "j", "🇨🇳 Chinês": "z"
}
VOICES = {
    "🇺🇸 Inglês": {"🇺🇸♂️ Santa": "am_santa", "🇺🇸♀️ Alloy": "af_alloy", "🇺🇸♀️ Aoede": "af_aoede", "🇺🇸♀️ Bella": "af_bella", "🇺🇸♀️ Heart": "af_heart", "🇺🇸♀️ Jessica": "af_jessica", "🇺🇸♀️ Kore": "af_kore", "🇺🇸♀️ Nicole": "af_nicole", "🇺🇸♀️ Nova": "af_nova", "🇺🇸♀️ River": "af_river", "🇺🇸♀️ Sarah": "af_sarah", "🇺🇸♀️ Sky": "af_sky", "🇺🇸♂️ Adam": "am_adam", "🇺🇸♂️ Echo": "am_echo", "🇺🇸♂️ Eric": "am_eric", "🇺🇸♂️ Fenrir": "am_fenrir", "🇺🇸♂️ Liam": "am_liam", "🇺🇸♂️ Michael": "am_michael", "🇺🇸♂️ Onyx": "am_onyx", "🇺🇸♂️ Puck": "am_puck"},
    "🇬🇧 Inglês Britânico": {"🇬🇧♀️ Alice": "bf_alice", "🇬🇧♀️ Emma": "bf_emma", "🇬🇧♀️ Isabella": "bf_isabella", "🇬🇧♀️ Lily": "bf_lily", "🇬🇧♂️ Daniel": "bm_daniel", "🇬🇧♂️ Fable": "bm_fable", "🇬🇧♂️ George": "bm_george", "🇬🇧♂️ Lewis": "bm_lewis"},
    "🇪🇸 Espanhol": {"🇪🇸♀️ Dora": "ef_dora", "🇪🇸♂️ Alex": "em_alex", "🇪🇸♂️ Santa": "em_santa"},
    "🇫🇷 Francês": {"🇫🇷♀️ Siwis": "ff_siwis"},
    "🇮🇳 Indiano": {"🇮🇳♀️ Alpha": "hf_alpha", "🇮🇳♀️ Beta": "hf_beta", "🇮🇳♂️ Omega": "hm_omega", "🇮🇳♂️ Psi": "hm_psi"},
    "🇮🇹 Italiano": {"🇮🇹♀️ Sara": "if_sara", "🇮🇹♂️ Nicola": "im_nicola"},
    "🇯🇵 Japonês": {"🇯🇵♀️ Alpha": "jf_alpha", "🇯🇵♀️ Gongitsune": "jf_gongitsune", "🇯🇵♀️ Nezumi": "jf_nezumi", "🇯🇵♀️ Tebukuro": "jf_tebukuro", "🇯🇵♂️ Kumo": "jm_kumo"},
    "🇧🇷 Português Brasileiro": {"🇧🇷♀️ Dora": "pf_dora", "🇧🇷♂️ Alex": "pm_alex", "🇧🇷♂️ Santa": "pm_santa"},
    "🇨🇳 Chinês": {"🇨🇳♀️ Xiaobei": "zf_xiaobei", "🇨🇳♀️ Xiaoni": "zf_xiaoni", "🇨🇳♀️ Xiaoxiao": "zf_xiaoxiao", "🇨🇳♀️ Xiaoyi": "zf_xiaoyi", "🇨🇳♂️ Yunjian": "zm_yunjian", "🇨🇳♂️ Yunxi": "zm_yunxi", "🇨🇳♂️ Yunxia": "zm_yunxia", "🇨🇳♂️ Yunyang": "zm_yunyang"}
}

# --- Cache de Pipelines ---
pipeline_cache = {}
def get_pipeline(lang_key):
    lang_code = LANGUAGES[lang_key]
    if lang_code not in pipeline_cache:
        print(f"Inicializando pipeline para o idioma: {lang_key} ({lang_code})")
        pipeline_cache[lang_code] = KPipeline(lang_code=lang_code)
    return pipeline_cache[lang_code]

# --- LÓGICA DE SRT REESTRUTURADA PARA SEGUIR O PADRÃO DE REFERÊNCIA ---

async def process_srt_file_kokoro_async(srt_file_path, language, voice_model, srt_temp_deleta):
    """
    Versão simplificada que gera seu formato nativo (.wav) e confia na nova
    função de mesclagem universal para lidar com ele.
    """
    # Importações "just-in-time" para robustez
    import sys
    from pathlib import Path
    try:
        from utils_file import timetoms, merge_audio_files, adjust_audio_speed
        from pydub import AudioSegment
    except ImportError:
        root_dir = Path(__file__).parent.parent.parent.resolve()
        if str(root_dir) not in sys.path: sys.path.insert(0, str(root_dir))
        from utils_file import timetoms, merge_audio_files, adjust_audio_speed
        from pydub import AudioSegment

    pipeline = get_pipeline(language)
    voice_code = VOICES[language][voice_model]
    
    srt_filename_stem = Path(srt_file_path).stem
    output_dir = Path(f"output/srt_temp_{srt_filename_stem}")
    if output_dir.exists(): shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    subs = pysrt.open(srt_file_path, encoding='utf-8-sig')
    max_retries = 3

    with tqdm(total=len(subs), desc="Gerando e ajustando áudios (WAV)", unit="legenda") as pbar:
        for sub in subs:
            # USAREMOS O PADDING DE 4 DÍGITOS PARA CONSISTÊNCIA
            final_segment_file = output_dir / f"{sub.index:04d}.wav"
            temp_tts_file = output_dir / f"{sub.index:04d}_temp.wav"
            target_duration_ms = timetoms(sub.end) - timetoms(sub.start)

            if target_duration_ms <= 0:
                AudioSegment.silent(duration=0).export(str(final_segment_file), format="wav")
                pbar.update(1)
                continue

            success = False
            for attempt in range(max_retries):
                try:
                    generator = pipeline(sub.text, voice=voice_code)
                    audio_chunks = [audio for _, _, audio in generator]
                    if not audio_chunks: continue

                    full_audio = np.concatenate(audio_chunks)
                    await asyncio.to_thread(sf.write, str(temp_tts_file), full_audio, 24000)

                    if temp_tts_file.exists() and temp_tts_file.stat().st_size > 1024:
                        await adjust_audio_speed(str(temp_tts_file), str(final_segment_file), target_duration_ms)
                        os.remove(temp_tts_file)
                        success = True
                        break
                    else: # Limpa arquivo inválido
                        if temp_tts_file.exists(): os.remove(temp_tts_file)

                except Exception:
                    if temp_tts_file.exists(): os.remove(temp_tts_file)
            
            if not success:
                silent_segment = AudioSegment.silent(duration=target_duration_ms)
                silent_segment.export(str(final_segment_file), format="wav")

            pbar.update(1)

    print("Todas as legendas processadas. Juntando o áudio final...")
    final_audio_path = await merge_audio_files(output_dir, srt_file_path)
    
    if srt_temp_deleta:
        shutil.rmtree(output_dir, ignore_errors=True)
    
    return final_audio_path

def controlador_process_srt_file_kokoro(srt_file_obj, language, voice_model, srt_temp_deleta):
    """Controlador síncrono que o Gradio chama. Ele executa a lógica assíncrona."""
    try:
        # Esta linha é a ponte entre o mundo síncrono (Gradio) e o assíncrono (nosso processamento)
        return asyncio.run(process_srt_file_kokoro_async(srt_file_obj.name, language, voice_model, srt_temp_deleta))
    except Exception as e:
        raise gr.Error(f"Ocorreu um erro no processamento SRT do Kokoro: {e}")

# --- Contrato do Addon (Funções que o app.py chama) ---

def get_name():
    return "Kokoro-TTS"

def create_ui():
    with gr.Column() as ui_block:
        gr.Markdown("Use as vozes do modelo Kokoro TTS.")
        with gr.Row():
            language_input = gr.Dropdown(choices=list(LANGUAGES.keys()), label="Idioma", value="🇧🇷 Português Brasileiro")
            initial_voices = list(VOICES["🇧🇷 Português Brasileiro"].keys())
            voice_model_input = gr.Dropdown(choices=initial_voices, label="Modelo de Voz", value=initial_voices[0] if initial_voices else None)
        audio_input = gr.Textbox(label="Texto", value='Olá, mundo! A inteligência artificial é incrível.', interactive=True)
        speed_input = gr.Slider(minimum=0.5, maximum=2.0, step=0.1, label="Velocidade", value=1.0, interactive=True)
        def update_voice_list(language):
            options = list(VOICES.get(language, {}).keys())
            return gr.update(choices=options, value=options[0] if options else None)
        language_input.change(fn=update_voice_list, inputs=language_input, outputs=voice_model_input)
    inputs = [audio_input, language_input, voice_model_input, speed_input]
    return ui_block, inputs

def generate_audio(text, language, voice_model, speed):
    if not text: raise gr.Error("O campo de texto não pode estar vazio.")
    if not language: raise gr.Error("Nenhum idioma selecionado.")
    if not voice_model: raise gr.Error("Nenhum modelo de voz selecionado.")
    try:
        pipeline = get_pipeline(language)
        voice_code = VOICES[language][voice_model]
        generator = pipeline(text, voice=voice_code, speed=speed)
        full_audio = [audio for _, _, audio in generator]
        if not full_audio: raise gr.Error("A geração de áudio falhou e não retornou dados.")
        concatenated_audio = np.concatenate(full_audio)
        output_dir = Path("output"); output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "kokoro_audio.wav"
        sf.write(output_file, concatenated_audio, 24000)
        return str(output_file)
    except Exception as e:
        raise gr.Error(f"Falha na geração de áudio do Kokoro. Erro: {e}")

def create_lote_ui():
    with gr.Column() as ui_block:
        gr.Markdown("Gere um único arquivo de áudio a partir do conteúdo de um arquivo .txt.")
        with gr.Row():
            language_input = gr.Dropdown(choices=list(LANGUAGES.keys()), label="Idioma", value="🇧🇷 Português Brasileiro")
            initial_voices = list(VOICES["🇧🇷 Português Brasileiro"].keys())
            voice_model_input = gr.Dropdown(choices=initial_voices, label="Modelo de Voz", value=initial_voices[0] if initial_voices else None)
        speed_input = gr.Slider(minimum=0.5, maximum=2.0, step=0.1, label="Velocidade", value=1.0, interactive=True)
        def update_voice_list(language):
            options = list(VOICES.get(language, {}).keys())
            return gr.update(choices=options, value=options[0] if options else None)
        language_input.change(fn=update_voice_list, inputs=language_input, outputs=voice_model_input)
    inputs = [language_input, voice_model_input, speed_input]
    return ui_block, inputs

def process_lote(file_obj, language, voice_model, speed):
    if not file_obj: raise gr.Error("Nenhum arquivo .txt enviado.")
    try:
        with open(file_obj.name, 'r', encoding='utf-8') as f:
            text_from_file = f.read()
        if not text_from_file.strip(): raise gr.Error("O arquivo .txt está vazio.")
        return generate_audio(text_from_file, language, voice_model, speed)
    except Exception as e:
        raise gr.Error(f"Falha ao processar o arquivo .txt. Erro: {e}")

def create_srt_ui():
    with gr.Column() as ui_block:
        gr.Markdown("Gere e sincronize áudio para um arquivo de legenda (.srt). A velocidade é ajustada automaticamente para cada legenda.")
        with gr.Row():
            language_input_srt = gr.Dropdown(choices=list(LANGUAGES.keys()), label="Idioma", value="🇧🇷 Português Brasileiro")
            initial_voices_srt = list(VOICES.get("🇧🇷 Português Brasileiro", {}).keys())
            voice_model_input_srt = gr.Dropdown(choices=initial_voices_srt, label="Modelo de Voz", value=initial_voices_srt[0] if initial_voices_srt else None)
        checkbox_deletar_temp_srt = gr.Checkbox(label="Apagar arquivos temporários após a conclusão", value=True, interactive=True)
        def update_voice_list_srt(language):
            options = list(VOICES.get(language, {}).keys())
            return gr.update(choices=options, value=options[0] if options else None)
        language_input_srt.change(fn=update_voice_list_srt, inputs=language_input_srt, outputs=voice_model_input_srt)
    inputs = [language_input_srt, voice_model_input_srt, checkbox_deletar_temp_srt]
    return ui_block, inputs

def process_srt(file_obj, language, voice_model, srt_temp_deleta):
    """Função do contrato do addon que chama o controlador síncrono."""
    if not file_obj: raise gr.Error("Nenhum arquivo .srt enviado.")
    if not voice_model: raise gr.Error("Nenhum modelo de voz selecionado.")
    return controlador_process_srt_file_kokoro(file_obj, language, voice_model, srt_temp_deleta)