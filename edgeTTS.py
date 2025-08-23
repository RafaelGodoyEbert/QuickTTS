# edgeTTS.py

import subprocess
import os
import json
import asyncio
from pathlib import Path
import pysrt
from tqdm import tqdm
import shutil

# Importa funções do nosso arquivo de utilidades
from utils import remove_silence, timetoms, merge_audio_files, adjust_audio_speed

# --- Funções de Gerenciamento de Voz ---
def load_voices():
    with open('voices.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_voice_options(language, voices_data):
    if language in voices_data:
        return [f"{voice['name']} | {voice['gender']}" for voice in voices_data[language]]
    return []

def extract_voice_name(formatted_voice):
    return formatted_voice.split(" | ")[0]

# --- Funções de Geração de Áudio (Edge-TTS) ---
def generate_audio(texto, modelo_de_voz, velocidade, tom, volume):
    actual_voice = extract_voice_name(modelo_de_voz)
    rate_str = f"+{velocidade}%" if velocidade >= 0 else f"{velocidade}%"
    pitch_str = f"+{tom}Hz" if tom >= 0 else f"{tom}Hz"
    volume_str = f"+{volume}%" if volume >= 0 else f"{volume}%"
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "new_audio.mp3")
    
    cmd = ["edge-tts", "--rate=" + rate_str, "--pitch=" + pitch_str, "--volume=" + volume_str,
           "-v", actual_voice, "-t", texto, "--write-media", output_file]
    
    print("Gerando áudio com Edge-TTS...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Áudio gerado com sucesso!")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Erro ao gerar áudio: {e.stderr}")
        return None

def generate_audio_from_file(file_path, modelo_de_voz, velocidade, tom, volume):
    actual_voice = extract_voice_name(modelo_de_voz)
    rate_str = f"+{velocidade}%" if velocidade >= 0 else f"{velocidade}%"
    pitch_str = f"+{tom}Hz" if tom >= 0 else f"{tom}Hz"
    volume_str = f"+{volume}%" if volume >= 0 else f"{volume}%"
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "new_audio.mp3")
    
    cmd = ["edge-tts", "-f", file_path, "--rate=" + rate_str, "--pitch=" + pitch_str,
           "--volume=" + volume_str, "-v", actual_voice, "--write-media", output_file]
    
    print("Gerando áudio do arquivo com Edge-TTS...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Áudio gerado com sucesso!")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Erro ao gerar áudio do arquivo: {e.stderr}")
        return None

# --- Funções Controladoras (Edge-TTS) ---
def controlador_generate_audio(audio_input, voice_model_input, speed, pitch, volume, cut_silence):
    audio_file = generate_audio(audio_input, voice_model_input, speed, pitch, volume)
    if audio_file and cut_silence:
        print("Removendo silêncio...")
        remove_silence(audio_file, audio_file)
        print("Silêncio removido.")
    return audio_file

def controlador_generate_audio_from_file(file, voice_model_input, speed, pitch, volume, cut_silence):
    if not file: return None
    audio_file = generate_audio_from_file(file.name, voice_model_input, speed, pitch, volume)
    if audio_file and cut_silence:
        print("Cortando silêncio...")
        remove_silence(audio_file, audio_file)
        print("Silêncio removido com sucesso!")
    return audio_file

# --- Lógica de Processamento de SRT (Usa Edge-TTS) ---
async def process_srt_file(srt_file_path, voice, output_dir_str, pitch, volume, srt_temp_deleta, progress=None):
    from edge_tts import Communicate as EdgeTTS
    from pydub import AudioSegment # Adicionado para gerar silêncio

    subs = pysrt.open(srt_file_path)
    output_dir = Path(output_dir_str)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pitch_str = f"+{pitch}Hz" if pitch >= 0 else f"{pitch}Hz"
    volume_str = f"+{volume}%" if volume >= 0 else f"{volume}%"
    max_retries = 3 # Número de tentativas para cada legenda

    with tqdm(total=len(subs), desc="Gerando e ajustando áudios com EdgeTTS", unit="segmento") as pbar:
        for sub in subs:
            output_file = output_dir / f"{sub.index:02d}.mp3"
            temp_file = output_dir / f"{sub.index:02d}_temp.mp3"
            target_duration_ms = timetoms(sub.end) - timetoms(sub.start)

            # Só processa se o arquivo final não existir
            if not output_file.exists() or output_file.stat().st_size == 0:
                success = False
                # Loop de retentativa
                for attempt in range(max_retries):
                    try:
                        tts_edge = EdgeTTS(text=sub.text, voice=voice, pitch=pitch_str, volume=volume_str)
                        await tts_edge.save(str(temp_file))
                        
                        # Verifica se o arquivo foi realmente criado e não está vazio
                        if temp_file.exists() and temp_file.stat().st_size > 0:
                            await adjust_audio_speed(str(temp_file), str(output_file), target_duration_ms)
                            os.remove(temp_file)
                            success = True
                            break # Sai do loop de retentativa se tiver sucesso
                        else:
                            print(f"Aviso: Tentativa {attempt + 1} para o índice {sub.index} falhou (arquivo não criado). Retentando...")

                    except Exception as e:
                        print(f"Aviso: Tentativa {attempt + 1} para o índice {sub.index} falhou com erro: {e}. Retentando...")
                    
                    await asyncio.sleep(1) # Espera 1 segundo antes da próxima tentativa
                
                # Se todas as tentativas falharem, gera silêncio
                if not success:
                    print(f"ERRO: Todas as {max_retries} tentativas falharam para o índice {sub.index}. Gerando silêncio.")
                    silent_segment = AudioSegment.silent(duration=target_duration_ms)
                    silent_segment.export(str(output_file), format="mp3")

            pbar.update(1)

    final_audio = await merge_audio_files(output_dir, srt_file_path)
    
    if srt_temp_deleta:
        shutil.rmtree(output_dir, ignore_errors=True)
        print(f"Pasta temporária {output_dir} apagada.")
    
    return final_audio

def controlador_process_srt_file(srt_file, voice_model_input, pitch, volume, srt_temp_deleta, progress=None):
    if not srt_file: return None
    actual_voice = extract_voice_name(voice_model_input)
    srt_filename_stem = Path(srt_file.name).stem
    output_dir = f"output/srt_temp_{srt_filename_stem}"
    
    return asyncio.run(process_srt_file(srt_file.name, actual_voice, output_dir, pitch, volume, srt_temp_deleta))