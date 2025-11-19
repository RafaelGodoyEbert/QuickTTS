# vevo_integration.py

import os
import sys
import torch
import torchaudio
import numpy as np
import gradio as gr

# --- Gerenciamento de Caminho e Diretório ---
original_cwd = os.getcwd()
amphion_path = os.path.abspath("Amphion")

if amphion_path not in sys.path:
    sys.path.append(amphion_path)

os.chdir(amphion_path)
print(f"Diretório de trabalho alterado para: {os.getcwd()}")

try:
    # Não vamos mais importar 'save_audio' para evitar problemas
    from models.vc.vevo.vevo_utils import VevoInferencePipeline
    print("Módulos do Amphion importados com sucesso.")
except ImportError as e:
    print(f"ERRO: Falha ao importar módulos do Amphion. Erro: {e}")
    os.chdir(original_cwd)
    raise

os.chdir(original_cwd)
print(f"Diretório de trabalho restaurado para: {os.getcwd()}")


# --- Variáveis Globais para Caching ---
inference_pipeline = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _get_vevo_pipeline():
    """Inicializa e armazena em cache o pipeline de inferência do Vevo."""
    global inference_pipeline
    if inference_pipeline is not None:
        return inference_pipeline

    print("Inicializando o pipeline Vevo-Timbre pela primeira vez...")
    
    os.chdir(amphion_path)
    print(f"Diretório de trabalho alterado para (inicialização): {os.getcwd()}")

    try:
        base_path = "ckpts/Vevo"
        content_style_tokenizer_ckpt_path = os.path.join(base_path, "tokenizer/vq8192")
        fmt_cfg_path = "models/vc/vevo/config/Vq8192ToMels.json"
        fmt_ckpt_path = os.path.join(base_path, "acoustic_modeling/Vq8192ToMels")
        vocoder_cfg_path = "models/vc/vevo/config/Vocoder.json"
        vocoder_ckpt_path = os.path.join(base_path, "acoustic_modeling/Vocoder")
        
        inference_pipeline = VevoInferencePipeline(
            content_style_tokenizer_ckpt_path=content_style_tokenizer_ckpt_path,
            fmt_cfg_path=fmt_cfg_path,
            fmt_ckpt_path=fmt_ckpt_path,
            vocoder_cfg_path=vocoder_cfg_path,
            vocoder_ckpt_path=vocoder_ckpt_path,
            device=device,
        )
        print("Pipeline Vevo-Timbre inicializado.")
    
    finally:
        os.chdir(original_cwd)
        print(f"Diretório de trabalho restaurado para (pós-inicialização): {os.getcwd()}")

    return inference_pipeline


def _process_audio(audio_path, target_sr=24000):
    """Carrega, reamostra e normaliza um áudio."""
    wav, sr = torchaudio.load(audio_path)
    
    if wav.shape[0] > 1:
        wav = torch.mean(wav, dim=0, keepdim=True)
        
    if sr != target_sr:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
        wav = resampler(wav)
        
    wav = wav / (torch.max(torch.abs(wav)) + 1e-6) * 0.95
    return wav, target_sr
    

def run_vevo_timbre_inference(source_audio_path, reference_audio_path):
    """Executa a clonagem de voz (timbre) usando o Vevo."""
    if not source_audio_path or not reference_audio_path:
        raise gr.Error("Áudio de origem e de referência são necessários!")

    print(f"Iniciando clonagem Vevo-Timbre. Origem: {source_audio_path}, Referência: {reference_audio_path}")
    
    pipeline = _get_vevo_pipeline()

    temp_dir = os.path.join(original_cwd, "temp")
    output_dir = os.path.join(original_cwd, "output")
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    temp_content_path = os.path.join(temp_dir, "vevo_source_processed.wav")
    temp_reference_path = os.path.join(temp_dir, "vevo_ref_processed.wav")
    output_path = os.path.join(output_dir, "cloned_vevo_timbre.wav")

    source_wav, sr = _process_audio(source_audio_path)
    ref_wav, _ = _process_audio(reference_audio_path)
    torchaudio.save(temp_content_path, source_wav, sr)
    torchaudio.save(temp_reference_path, ref_wav, sr)

    os.chdir(amphion_path)
    print(f"Diretório de trabalho alterado para (inferência): {os.getcwd()}")
    
    try:
        print("Executando a inferência do Vevo...")
        gen_audio = pipeline.inference_fm(
            src_wav_path=temp_content_path,
            timbre_ref_wav_path=temp_reference_path,
            flow_matching_steps=32,
        )
        
        # ***** LINHA CORRIGIDA ABAIXO *****
        # Usaremos torchaudio.save diretamente para evitar problemas com a função do Amphion.

        # 1. Garante que o tensor está na CPU
        if gen_audio.is_cuda:
            gen_audio = gen_audio.cpu()

        # 2. Normaliza o áudio para o range [-1, 1] para evitar clipping
        max_val = torch.max(torch.abs(gen_audio))
        if max_val > 1.0:
            normalized_audio = gen_audio / max_val
        else:
            normalized_audio = gen_audio

        # 3. Salva usando torchaudio com a taxa de amostragem correta (24kHz, padrão do Vevo)
        torchaudio.save(output_path, normalized_audio, 24000)
        
        print(f"Áudio clonado salvo em: {output_path}")
        
        return output_path

    except Exception as e:
        print(f"Ocorreu um erro durante a inferência do Vevo: {e}")
        import traceback
        traceback.print_exc()
        raise gr.Error(f"Falha na clonagem com Vevo: {e}")
    finally:
        os.chdir(original_cwd)
        print(f"Diretório de trabalho restaurado para (pós-inferência): {os.getcwd()}")
        if os.path.exists(temp_content_path):
            os.remove(temp_content_path)
        if os.path.exists(temp_reference_path):
            os.remove(temp_reference_path)