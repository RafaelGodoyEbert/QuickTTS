# tiktokTTS.py

import os
import sys
from pathlib import Path
import gradio as gr
import asyncio
import pysrt
from tqdm import tqdm
import shutil

# Importa funções utilitárias
from utils import remove_silence, timetoms, merge_audio_files, adjust_audio_speed

# --- Configuração e Imports da Biblioteca TikTok ---
try:
    sys.path.append(str(Path(__file__).parent / "TikTok_TTS"))
    from TikTok_TTS.tiktok_voice import Voice, tts
    TIKTOK_TTS_AVAILABLE = True
    print("Biblioteca TikTok TTS carregada com sucesso.")
except ImportError:
    TIKTOK_TTS_AVAILABLE = False
    print("Aviso: Biblioteca TikTok TTS não encontrada. A funcionalidade estará desabilitada.")
    class Voice: pass
    def tts(*args, **kwargs): pass

# --- DICIONÁRIO DE VOZES CATEGORIZADAS ---
TIKTOK_VOICES_CATEGORIZED = {
    'Português (Brasil)': [
        'BR_FEMALE_1', 'BR_FEMALE_2', 'BR_FEMALE_3', 'BR_MALE', 
        'BP_FEMALE_IVETE', 'BP_FEMALE_LUDMILLA', 'PT_FEMALE_LHAYS', 'PT_FEMALE_LAIZZA', 'PT_MALE_BUENO'
    ],
    'Inglês (EUA)': [
        'US_FEMALE_1', 'US_FEMALE_2', 'US_MALE_1', 'US_MALE_2', 'US_MALE_3', 'US_MALE_4'
    ],
    'Inglês (Reino Unido)': ['UK_MALE_1', 'UK_MALE_2'],
    'Inglês (Austrália)': ['AU_FEMALE_1', 'AU_MALE_1'],
    'Inglês (Personagens Especiais)': [
        'MALE_JOMBOY', 'MALE_CODY', 'FEMALE_SAMC', 'FEMALE_MAKEUP', 'FEMALE_RICHGIRL', 
        'MALE_ASHMAGIC', 'MALE_OLANTERKKERS', 'MALE_UKNEIGHBOR', 'MALE_UKBUTLER', 
        'FEMALE_SHENNA', 'FEMALE_PANSINO', 'MALE_TREVOR', 'FEMALE_BETTY', 'MALE_CUPID', 
        'FEMALE_GRANDMA', 'MALE_NARRATION', 'MALE_FUNNY', 'FEMALE_EMOTIONAL'
    ],
    'Inglês Personagens (Filmes e Outros)': [
        'GHOSTFACE', 'CHEWBACCA', 'C3PO', 'STITCH', 'STORMTROOPER', 'ROCKET', 
        'MADAME_LEOTA', 'GHOST_HOST', 'PIRATE', 'MALE_GRINCH', 'MALE_DEADPOOL', 'MALE_JARVIS'
    ],
    'Inglês Personagens (Festivos)': [
        'MALE_XMXS_CHRISTMAS', 'MALE_SANTA_NARRATION', 'MALE_SANTA_EFFECT', 
        'FEMALE_HT_NEYEAR', 'MALE_WIZARD', 'FEMALE_HT_HALLOWEEN'
    ],
    'Inglês Cantores / Músicas': [
        'MALE_SING_DEEP_JINGLE', 'SING_FEMALE_ALTO', 'SING_MALE_TENOR', 'SING_FEMALE_WARMY_BREEZE',
        'SING_MALE_SUNSHINE_SOON', 'SING_FEMALE_GLORIOUS', 'SING_MALE_IT_GOES_UP', 
        'SING_MALE_CHIPMUNK', 'SING_FEMALE_WONDERFUL_WORLD', 'SING_MALE_FUNNY_THANKSGIVING'
    ],
    'Japonês': [
        'JP_FEMALE_1', 'JP_FEMALE_2', 'JP_FEMALE_3', 'JP_MALE', 'JP_FEMALE_FUJICOCHAN', 
        'JP_FEMALE_HASEGAWARIONA', 'JP_MALE_KEIICHINAKANO', 'JP_FEMALE_OOMAEAIIKA', 
        'JP_MALE_YUJINCHIGUSA', 'JP_FEMALE_SHIROU', 'JP_MALE_TAMAWAKAZUKI', 
        'JP_FEMALE_KAORISHOJI', 'JP_FEMALE_YAGISHAKI', 'JP_MALE_HIKAKIN', 'JP_FEMALE_REI',
        'JP_MALE_SHUICHIRO', 'JP_MALE_MATSUDAKE', 'JP_FEMALE_MACHIKORIIITA', 
        'JP_MALE_MATSUO', 'JP_MALE_OSADA'
    ],
    'Coreano': ['KR_MALE_1', 'KR_FEMALE', 'KR_MALE_2'],
    'Espanhol': ['ES_MALE', 'ES_MX_MALE'],
    'Francês': ['FR_MALE_1', 'FR_MALE_2'],
    'Alemão': ['DE_FEMALE', 'DE_MALE'],
    'Indonésio': ['ID_FEMALE']
}

def get_tiktok_voice_options(language):
    return TIKTOK_VOICES_CATEGORIZED.get(language, [])

# --- Função Controladora de Texto/Arquivo ---
def controlador_generate_audio_tiktok(voice_str, text, text_file, cut_silence):
    if not TIKTOK_TTS_AVAILABLE:
        raise gr.Error("A biblioteca TikTok TTS não está instalada ou configurada corretamente.")
    if not text and text_file is None:
        raise gr.Error("Por favor, forneça um texto ou um arquivo .txt para gerar o áudio.")

    output_dir = "output"; os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "tiktok_audio.mp3")
    input_text = text if text else Path(text_file.name).read_text(encoding='utf-8')
    
    try:
        print(f"Gerando áudio com a voz TikTok: {voice_str}...")
        tts(input_text, Voice[voice_str], output_file)
        print("Áudio TikTok gerado com sucesso!")
        if cut_silence:
            print("Removendo silêncio do áudio TikTok..."); remove_silence(output_file, output_file); print("Silêncio removido.")
        return output_file
    
    except requests.exceptions.RequestException as e:
        print(f"!!! TIKTOK TTS NETWORK ERROR DETECTED: {e}")
        raise gr.Error(TIKTOK_CONNECTION_ERROR_MSG)
    except KeyError:
        raise gr.Error(f"A voz '{voice_str}' não foi encontrada.")
    except Exception as e:
        print(f"!!! TIKTOK TTS UNEXPECTED ERROR: {type(e).__name__} - {e}")
        raise gr.Error(f"Ocorreu um erro inesperado no TikTok TTS, se tiver usando GRADIO, mude pra Google Colab: {e}")

# --- NOVA LÓGICA DE PROCESSAMENTO DE SRT PARA TIKTOK ---

async def process_srt_file_tiktok(srt_file_path, voice_str, output_dir_str, srt_temp_deleta, progress=None):
    subs = pysrt.open(srt_file_path)
    output_dir = Path(output_dir_str)
    output_dir.mkdir(parents=True, exist_ok=True)
    max_retries = 3 # Número de tentativas para cada legenda

    with tqdm(total=len(subs), desc="Gerando e ajustando áudios com TikTok", unit="segmento") as pbar:
        for sub in subs:
            output_file = output_dir / f"{sub.index:02d}.mp3"
            temp_file = output_dir / f"{sub.index:02d}_temp.mp3"
            target_duration_ms = timetoms(sub.end) - timetoms(sub.start)

            if not output_file.exists() or output_file.stat().st_size == 0:
                success = False
                for attempt in range(max_retries):
                    try:
                        await asyncio.to_thread(tts, sub.text, Voice[voice_str], str(temp_file))
                        
                        if temp_file.exists() and temp_file.stat().st_size > 0:
                            await adjust_audio_speed(str(temp_file), str(output_file), target_duration_ms)
                            os.remove(temp_file)
                            success = True
                            break
                        else:
                            print(f"Aviso: Tentativa {attempt + 1} para o índice {sub.index} (TikTok) falhou. Retentando...")

                    except Exception as e:
                        print(f"Aviso: Tentativa {attempt + 1} para o índice {sub.index} (TikTok) falhou com erro: {e}. Retentando...")
                    
                    await asyncio.sleep(1)

                if not success:
                    print(f"ERRO: Todas as {max_retries} tentativas (TikTok) falharam para o índice {sub.index}. Gerando silêncio.")
                    silent_segment = AudioSegment.silent(duration=target_duration_ms)
                    silent_segment.export(str(output_file), format="mp3")

            pbar.update(1)

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
        return asyncio.run(process_srt_file_tiktok(srt_file.name, voice_str, output_dir, srt_temp_deleta, progress=progress))
    
    except requests.exceptions.RequestException as e:
        print(f"!!! TIKTOK TTS NETWORK ERROR (SRT): {e}")
        raise gr.Error(TIKTOK_CONNECTION_ERROR_MSG)
    except Exception as e:
        print(f"!!! TIKTOK TTS UNEXPECTED ERROR (SRT): {e}")
        raise gr.Error(f"Ocorreu um erro inesperado no TikTok TTS, se tiver usando GRADIO, mude pra Google Colab: {e}")