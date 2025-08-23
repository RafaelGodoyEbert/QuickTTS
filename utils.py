# utils.py

import os
import subprocess
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import split_on_silence
import pysrt
from tqdm import tqdm
import asyncio

def remove_silence(input_file, output_file):
    """Lê um arquivo MP3, remove o silêncio e salva como MP3 com alta qualidade, mantendo pequenas pausas."""
    audio = AudioSegment.from_mp3(input_file)
    segments = split_on_silence(
        audio,
        min_silence_len=500,
        silence_thresh=-40,
        keep_silence=250
    )
    non_silent_audio = AudioSegment.silent(duration=0)
    for segment in segments:
        non_silent_audio += segment
    non_silent_audio.export(output_file, format="mp3", bitrate="192k")

def timetoms(time_obj):
    """Converte um objeto de tempo do Pysrt para milissegundos."""
    return time_obj.hours * 3600000 + time_obj.minutes * 60000 + time_obj.seconds * 1000 + time_obj.milliseconds

# --- VERSÃO COMPLETAMENTE NOVA E ROBUSTA ---
async def adjust_audio_speed(input_file, output_file, target_duration_ms):
    """Ajusta a velocidade do áudio usando o filtro 'atempo' do FFmpeg para máxima qualidade."""
    
    # Usa ffprobe para obter a duração exata, é mais confiável que pydub
    try:
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", input_file
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        original_duration_ms = float(result.stdout.strip()) * 1000
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback para pydub se ffprobe não estiver disponível ou falhar
        original_duration_ms = len(AudioSegment.from_mp3(input_file))

    if original_duration_ms == 0 or target_duration_ms <= 0:
        silent_audio = AudioSegment.silent(duration=target_duration_ms)
        silent_audio.export(output_file, format="mp3", bitrate="192k")
        return silent_audio

    speed_factor = original_duration_ms / target_duration_ms

    # Se a velocidade já for quase perfeita, apenas renomeia para evitar re-compressão
    if 0.99 < speed_factor < 1.01:
        Path(input_file).rename(output_file)
        return AudioSegment.from_mp3(output_file)

    # Constrói a cadeia de filtros 'atempo'
    atempo_filters = []
    current_factor = speed_factor
    
    # Para aceleração > 2.0x
    while current_factor > 2.0:
        atempo_filters.append("atempo=2.0")
        current_factor /= 2.0
    
    # Para desaceleração < 0.5x
    while current_factor < 0.5:
        atempo_filters.append("atempo=0.5")
        current_factor /= 0.5

    # Adiciona o fator final (que agora está entre 0.5 e 2.0)
    if current_factor != 1.0:
        atempo_filters.append(f"atempo={current_factor:.5f}")

    filter_string = ",".join(atempo_filters)

    # Executa o comando FFmpeg
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", input_file, "-filter:a", filter_string,
        "-b:a", "192k", "-ar", "44100", # Define bitrate e sample rate de alta qualidade
        "-hide_banner", "-loglevel", "error", output_file
    ]

    try:
        # Roda o subprocesso bloqueante em uma thread separada para não congelar a UI
        proc = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f"Erro no FFmpeg ao ajustar a velocidade: {stderr.decode()}")
            # Em caso de erro, cria silêncio para não quebrar o processo
            silent = AudioSegment.silent(duration=target_duration_ms)
            silent.export(output_file, format="mp3")
    except FileNotFoundError:
        print("ERRO: FFmpeg não encontrado. Verifique se ele está instalado e no PATH do sistema.")
        raise
    
    return AudioSegment.from_mp3(output_file)


async def merge_audio_files(output_folder, srt_file_path):
    """Mescla segmentos de áudio baseados nos tempos de um arquivo SRT com sincronização correta."""
    subs = pysrt.open(srt_file_path)
    final_audio = AudioSegment.silent(duration=0)
    base_name = Path(srt_file_path).stem
    
    with tqdm(total=len(subs), desc=f"Mesclando áudios para {base_name}", unit="segmento") as pbar:
        for sub in subs:
            start_time_ms = timetoms(sub.start)
            end_time_ms = timetoms(sub.end)
            
            audio_file = Path(output_folder) / f"{sub.index:02d}.mp3"
            
            silence_duration = start_time_ms - len(final_audio)
            if silence_duration > 5: # Adiciona uma pequena margem para evitar micro-silêncios
                final_audio += AudioSegment.silent(duration=silence_duration)
            
            if audio_file.exists() and audio_file.stat().st_size > 0:
                audio_segment = AudioSegment.from_mp3(str(audio_file))
                final_audio += audio_segment
            else:
                segment_duration = end_time_ms - start_time_ms
                final_audio += AudioSegment.silent(duration=max(0, segment_duration))
            
            pbar.update(1)

    srt_output_dir = Path("output/srt_output")
    srt_output_dir.mkdir(parents=True, exist_ok=True)
    output_file_path = srt_output_dir / f"{base_name}_final.mp3"
    final_audio.export(str(output_file_path), format="mp3", bitrate="192k")
    print(f"\nÁudio final salvo em: {output_file_path}\n")
    return str(output_file_path)

def listar_audios():
    """Lista os arquivos de áudio na pasta de saída do SRT."""
    try:
        srt_output_dir = "output/srt_output"
        if not os.path.exists(srt_output_dir):
            os.makedirs(srt_output_dir, exist_ok=True)
            return ["Nenhum áudio gerado ainda"]
        arquivos = [f for f in os.listdir(srt_output_dir) if f.endswith(('.mp3', '.wav'))]
        return arquivos if arquivos else ["Nenhum áudio gerado ainda"]
    except Exception as e:
        print(f"Erro ao listar áudios: {e}")
        return ["Erro ao listar arquivos"]

def tocar_audio(arquivo):
    """Retorna o caminho completo para um arquivo de áudio selecionado para tocar."""
    if arquivo and arquivo != "Nenhum áudio gerado ainda":
        return f"output/srt_output/{arquivo}"
    return None