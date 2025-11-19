# install_vevo.py

import os
import sys
import importlib.util
import site
import torch
import subprocess
from huggingface_hub import snapshot_download

def setup_amphion_path():
    """Clona o repositório Amphion se não existir e o adiciona ao path do sistema."""
    if not os.path.exists("Amphion"):
        print("Clonando o repositório Amphion...")
        try:
            subprocess.run(["git", "clone", "https://github.com/open-mmlab/Amphion.git"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"ERRO: Falha ao clonar o repositório Amphion. Verifique se o Git está instalado. Erro: {e}")
            raise
    
    amphion_path = os.path.abspath("Amphion")
    
    # O Amphion precisa ser o diretório de trabalho atual para seus imports funcionarem
    # Mas só o adicionamos ao path por enquanto. A integração cuidará da mudança de diretório.
    if amphion_path not in sys.path:
        sys.path.append(amphion_path)
    
    return amphion_path

def install_espeak():
    """Detecta e instala a dependência espeak-ng se necessário (para sistemas baseados em Debian/Ubuntu)."""
    try:
        # Verifica se o comando 'espeak-ng' existe
        result = subprocess.run(["which", "espeak-ng"], capture_output=True, text=True)
        if result.returncode != 0:
            print("espeak-ng não detectado, tentando instalar via apt-get...")
            # Tenta usar 'sudo' se 'apt-get' falhar por permissão
            try:
                subprocess.run(["apt-get", "update"], check=True)
                subprocess.run(["apt-get", "install", "-y", "espeak-ng", "espeak-ng-data"], check=True)
            except PermissionError:
                print("Permissão negada. Tentando com 'sudo'...")
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", "espeak-ng", "espeak-ng-data"], check=True)
            print("espeak-ng e seus pacotes de dados foram instalados com sucesso!")
        else:
            print("espeak-ng já está instalado no sistema.")
    except FileNotFoundError:
        print("AVISO: O comando 'apt-get' não foi encontrado. Se você não estiver no Linux (Debian/Ubuntu), instale o 'espeak-ng' manualmente.")
    except Exception as e:
        print(f"Erro ao instalar espeak-ng: {e}")
        print("Por favor, tente instalar 'espeak-ng' manualmente.")

def patch_langsegment_init():
    """Aplica patch no __init__.py do LangSegment para compatibilidade."""
    try:
        init_path = None
        for site_pkg_path in site.getsitepackages():
            potential_path = os.path.join(site_pkg_path, 'LangSegment', '__init__.py')
            if os.path.exists(potential_path):
                init_path = potential_path
                break
        
        if not init_path:
             print("AVISO: Não foi possível localizar o pacote LangSegment para aplicar o patch.")
             return

        with open(init_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'setLangfilters' in content or 'getLangfilters' in content:
            print(f"Aplicando patch em {init_path}...")
            content = content.replace(',setLangfilters', '').replace(',getLangfilters', '')
            with open(init_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Patch aplicado com sucesso.")
        else:
            print("O patch para LangSegment não é necessário.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao aplicar o patch no LangSegment: {e}")

# Clone Amphion repository
if not os.path.exists("Amphion"):
    subprocess.run(["git", "clone", "https://github.com/open-mmlab/Amphion.git"])
    os.chdir("Amphion")
else:
    if not os.getcwd().endswith("Amphion"):
        os.chdir("Amphion")
        
def preload_all_vevo_resources():
    """Baixa todos os modelos e configurações necessários para o Vevo."""
    target_dir = os.path.join("Amphion", "ckpts", "Vevo")
    if os.path.exists(os.path.join(target_dir, "acoustic_modeling", "Vocoder")):
         print("Recursos do Vevo já parecem estar baixados. Pulando download.")
         return

    print("Iniciando o download de todos os recursos do Vevo (isso pode levar vários minutos)...")
    os.makedirs(target_dir, exist_ok=True)
    
    allow_patterns = [
        "config/*", "tokenizer/vq32/*", "tokenizer/vq8192/*",
        "contentstyle_modeling/*", "acoustic_modeling/*"
    ]
    
    try:
        snapshot_download(
            repo_id="amphion/Vevo", repo_type="model",
            local_dir=target_dir, local_dir_use_symlinks=False,
            allow_patterns=allow_patterns,
        )
        print("Download de todos os recursos do Vevo concluído!")
    except Exception as e:
        print(f"ERRO: Falha ao baixar os modelos do Vevo: {e}")
        raise

# A função que o app.py vai chamar
def setup_vevo():
    """Função principal que executa todas as etapas de configuração."""
    print("=== INICIANDO CONFIGURAÇÃO DO VEVO ===")
    # install_espeak() # Descomente se estiver rodando em um ambiente Linux
    setup_amphion_path()
    patch_langsegment_init()
    preload_all_vevo_resources()
    print("=== CONFIGURAÇÃO DO VEVO CONCLUÍDA ===")

if __name__ == "__main__":

    setup_vevo()
