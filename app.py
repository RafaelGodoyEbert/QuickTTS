# app.py (VERSÃO FINAL - Nenhuma alteração necessária aqui se a anterior estiver em uso)

import gradio as gr
import os
import json
from pathlib import Path
import importlib.util
import subprocess
import sys
import zipfile
import shutil
import tempfile
import traceback

log = False

if log:
    # ### INÍCIO DO CÓDIGO DE DEPURAÇÃO DE AMBIENTE ###
    print("\n" + "="*60)
    print("  VERIFICANDO AMBIENTE DE EXECUÇÃO DO APP.PY")
    print(f"  sys.executable (Qual Python está rodando este script):")
    print(f"  -> {sys.executable}")
    print("\n  sys.path (Onde este Python procura por módulos):")
    for path in sys.path:
        print(f"  -> {path}")
    print("="*60 + "\n")
    # ### FIM DO CÓDIGO DE DEPURAÇÃO ###

# Tenta importar o GitPython
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    print("Aviso: GitPython não está instalado (pip install GitPython). A instalação de addons via Git está desabilitada.")
    GIT_AVAILABLE = False

# --- Imports para clonagem de voz ---
import install_vevo
from vevo_integration import run_vevo_timbre_inference

# --- Imports dos módulos de cabeçalho e descrição ---
from header import badges, description

# --- Executa a configuração do Vevo ao iniciar o app ---
try:
    install_vevo.setup_vevo()
    VEVO_AVAILABLE = True
except Exception as e:
    print(f"AVISO: Falha na configuração do Vevo. A clonagem de voz pode não funcionar. Erro: {e}")
    VEVO_AVAILABLE = False

# --- Configurações Globais ---
ADDONS_DIR = "addons"
loaded_addons = {}
PROJECT_ROOT = Path(__file__).parent.resolve()

# --- GERENCIADOR DE ADDONS ---
def load_addons():
    print("--- Iniciando carregamento de addons ---")
    if not os.path.exists(ADDONS_DIR): os.makedirs(ADDONS_DIR)
    
    for addon_name in sorted(os.listdir(ADDONS_DIR)):
        addon_path = os.path.join(ADDONS_DIR, addon_name)
        if os.path.isdir(addon_path):
            manifest_path = os.path.join(addon_path, "manifest.json")
            if not os.path.exists(manifest_path): continue
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f: manifest = json.load(f)
                entry_point_name = manifest.get('entry_point', 'addon')
                entry_point_path = os.path.join(addon_path, f"{entry_point_name}.py")
                if not os.path.exists(entry_point_path): continue
                
                spec = importlib.util.spec_from_file_location(addon_name, entry_point_path)
                addon_module = importlib.util.module_from_spec(spec)
                sys.modules[addon_name] = addon_module
                
                if hasattr(addon_module, 'initialize'):
                    addon_module.initialize(PROJECT_ROOT)
                
                spec.loader.exec_module(addon_module)
                
                addon_display_name = addon_module.get_name()
                loaded_addons[addon_display_name] = addon_module
                print(f"- Addon '{addon_display_name}' carregado com sucesso.")
            except Exception as e:
                print(f"ERRO CRÍTICO: Falha ao carregar o addon '{addon_name}': {e}")
                traceback.print_exc()
    print(f"--- Carregamento finalizado. Total de addons carregados: {len(loaded_addons)} ---")

# --- FUNÇÕES DE INSTALAÇÃO (Sem alterações) ---
def _install_dependencies(addon_root_path, manifest, progress):
    if "requirements" in manifest and manifest["requirements"]:
        req_file = addon_root_path / manifest["requirements"]
        if req_file.exists():
            progress(0.7, desc=f"Instalando dependências de {req_file.name}...")
            
            if log:
                # --- INÍCIO DAS MUDANÇAS PARA DEPURAÇÃO ---
                print("="*50)
                print("INICIANDO DEPURAÇÃO DA INSTALAÇÃO DE DEPENDÊNCIAS")
                print(f"Executável Python sendo usado (sys.executable): {sys.executable}")
                print(f"Instalando a partir do arquivo: {req_file}")

                command = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
                print(f"Comando a ser executado: {' '.join(command)}")
                
            try:
                # Removemos o '-qq' para ver a saída completa do pip
                result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
                print("--- Saída do PIP (STDOUT): ---")
                print(result.stdout)
                print("--- Fim da Saída do PIP ---")
                if result.stderr:
                    print("--- Erros do PIP (STDERR): ---")
                    print(result.stderr)
                    print("--- Fim dos Erros do PIP ---")
                print("Dependências instaladas com sucesso pelo subprocesso.")

            except subprocess.CalledProcessError as e:
                print("!!! ERRO CRÍTICO DURANTE A INSTALAÇÃO VIA SUBPROCESSO !!!")
                print("--- Saída do PIP (STDOUT): ---")
                print(e.stdout)
                print("--- Fim da Saída do PIP ---")
                print("--- Erros do PIP (STDERR): ---")
                print(e.stderr)
                print("--- Fim dos Erros do PIP ---")
                raise RuntimeError(f"Falha ao instalar dependências. Verifique o log do terminal acima.")
            except Exception as e:
                print(f"Ocorreu um erro inesperado: {e}")
                raise
            finally:
                print("DEPURAÇÃO DA INSTALAÇÃO FINALIZADA")
                print("="*50)
            # --- FIM DAS MUDANÇAS ---
            
def install_addon_from_zip(zip_file, progress=gr.Progress()):
    if not zip_file: return "Erro: Nenhum arquivo enviado."
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            progress(0.1, desc="Extraindo arquivo ZIP..."); zipfile.ZipFile(zip_file.name, 'r').extractall(temp_dir)
            progress(0.4, desc="Verificando a estrutura..."); manifest_path = list(Path(temp_dir).rglob('manifest.json'))[0]
            addon_root = manifest_path.parent
            with open(manifest_path, 'r', encoding='utf-8') as f: manifest = json.load(f)
            addon_name = manifest.get("name", "addon_sem_nome")
            target_dir_name = addon_name.replace(" ", "_").lower() + "_addon"
            target_path = Path(ADDONS_DIR) / target_dir_name
            if target_path.exists(): raise FileExistsError(f"Um addon com o nome '{addon_name}' já existe.")
            _install_dependencies(addon_root, manifest, progress)
            progress(0.9, desc="Finalizando a instalação..."); shutil.move(str(addon_root), str(target_path))
        return f"Addon '{addon_name}' instalado com sucesso! Reinicie o aplicativo para ativá-lo."
    except Exception as e: return f"Ocorreu um erro durante a instalação: {e}"
def install_addon_from_git(repo_url, progress=gr.Progress()):
    # ... (código omitido para brevidade)
    pass

# --- FUNÇÕES DO APP PRINCIPAL ---
def load_samples(sample_dir="samples"):
    samples_path = Path(sample_dir)
    if not samples_path.exists(): return []
    examples = [[str(f), str(f.with_suffix(".mp3"))] for f in sorted(samples_path.glob("*.srt")) if f.with_suffix(".mp3").exists()]
    if not examples: print(f"Aviso: Nenhum par de exemplos (.srt, .mp3) encontrado em '{sample_dir}'.")
    return examples

def handle_voice_cloning(cloning_model, source_audio, reference_audio):
    if not source_audio: raise gr.Error("Gere um áudio de origem primeiro.")
    if not reference_audio: raise gr.Error("Faça o upload de um áudio de referência.")
    
    if cloning_model == "Vevo-Timbre":
        if not VEVO_AVAILABLE: raise gr.Error("Vevo não foi configurado corretamente.")
        
        # A função abaixo agora vai retornar o caminho do arquivo
        result_path = run_vevo_timbre_inference(source_audio, reference_audio)
        
        # Adicionamos um print para confirmar no terminal que o caminho foi recebido
        print(f"Caminho do áudio clonado retornado para o Gradio: {result_path}")
        
        return result_path
    else: 
        raise gr.Error(f"{cloning_model} ainda não está implementado.")

# --- INTERFACE GRADIO ---
load_addons()
with gr.Blocks(theme=gr.themes.Default(primary_hue="green", secondary_hue="blue"), title="QuickTTS") as iface:
    gr.Markdown(badges); gr.Markdown(description)
    addon_choices = list(loaded_addons.keys())
    with gr.Tabs():
        with gr.TabItem("TTS e Clonagem de Voz"):
            gr.Markdown("### Etapa 1: Gerar Áudio Base")
            if not addon_choices:
                gr.Markdown("<p style='color: red; text-align: center;'>Nenhum addon carregado.</p>")
                audio_output = gr.Audio(visible=False)
            else:
                provider_choice = gr.Radio(choices=addon_choices, value=addon_choices[0], label="Escolha o Provedor")
                addon_uis, addon_inputs = {}, {}
                for name, addon in loaded_addons.items():
                    with gr.Column(visible=(name == addon_choices[0])) as ui_wrapper:
                        ui_block, inputs = addon.create_ui()
                        addon_uis[name], addon_inputs[name] = ui_wrapper, inputs
                audio_output = gr.Audio(label="Resultado (Áudio de Origem)", type="filepath")
                with gr.Row():
                    gerar_button = gr.Button("Falar", variant="primary")
                    gr.ClearButton([audio_output], value='Limpar Áudio')
                def switch_provider_ui(p_name): return {ui: gr.update(visible=(n == p_name)) for n, ui in addon_uis.items()}
                provider_choice.change(fn=switch_provider_ui, inputs=provider_choice, outputs=list(addon_uis.values()))
                def dispatcher(p_name, *args):
                    addon, s_idx = loaded_addons[p_name], 0
                    for n, i in addon_inputs.items():
                        if n == p_name: return addon.generate_audio(*args[s_idx:s_idx+len(i)])
                        s_idx += len(i)
                all_inputs = [i for n in addon_choices for i in addon_inputs[n]]
                gerar_button.click(fn=dispatcher, inputs=[provider_choice] + all_inputs, outputs=audio_output)
            
            gr.Markdown("<hr>")
            gr.Markdown("### Etapa 2: Clonar a Voz (Opcional)")
            with gr.Accordion("Clone de voz", open=False):
                cloning_model_choice = gr.Radio(["Vevo-Timbre", "SeedVC"], value="Vevo-Timbre", label="Modelo")
                reference_audio_input = gr.Audio(label="Áudio de Referência", type="filepath")
                cloned_audio_output = gr.Audio(label="Resultado da Clonagem", type="filepath")
                clone_button = gr.Button("Clonar Voz", variant="primary", visible=VEVO_AVAILABLE)
            clone_button.click(fn=handle_voice_cloning, inputs=[cloning_model_choice, audio_output, reference_audio_input], outputs=cloned_audio_output, queue=True)

        with gr.TabItem("Lote (Arquivo txt)"):
            gr.Markdown("### Gere áudio a partir de um arquivo de texto (.txt)")
            lote_addons = {n: a for n, a in loaded_addons.items() if hasattr(a, 'create_lote_ui')}
            lote_choices = list(lote_addons.keys())
            if not lote_choices: gr.Markdown("<p style='color: red;'>Nenhum addon instalado suporta este modo.</p>")
            else:
                provider_choice_lote = gr.Radio(choices=lote_choices, value=lote_choices[0], label="Escolha o Provedor")
                file_input_lote = gr.File(label="Arquivo de Texto (.txt)", file_types=[".txt"])
                lote_uis, lote_inputs = {}, {}
                for name, addon in lote_addons.items():
                    with gr.Column(visible=(name == lote_choices[0])) as ui_wrapper:
                        ui_block, inputs = addon.create_lote_ui(); lote_uis[name], lote_inputs[name] = ui_wrapper, inputs
                audio_output_lote = gr.Audio(label="Resultado", type="filepath")
                gerar_lote_btn = gr.Button("Gerar Áudio do Arquivo", variant="primary")
                def switch_lote_ui(p_name): return {ui: gr.update(visible=(n == p_name)) for n, ui in lote_uis.items()}
                provider_choice_lote.change(fn=switch_lote_ui, inputs=provider_choice_lote, outputs=list(lote_uis.values()))
                def lote_dispatcher(p_name, f_obj, *args):
                    addon, s_idx = lote_addons[p_name], 0
                    for n, i in lote_inputs.items():
                        if n == p_name: return addon.process_lote(f_obj, *args[s_idx:s_idx+len(i)])
                        s_idx += len(i)
                all_lote_inputs = [i for n in lote_choices for i in lote_inputs[n]]
                gerar_lote_btn.click(fn=lote_dispatcher, inputs=[provider_choice_lote, file_input_lote] + all_lote_inputs, outputs=audio_output_lote, queue=True)

        with gr.TabItem("Ler .SRT"):
            gr.Markdown("### Gere e sincronize áudio para um arquivo de legenda (.srt)")
            srt_addons = {n: a for n, a in loaded_addons.items() if hasattr(a, 'create_srt_ui')}
            srt_choices = list(srt_addons.keys())
            if not srt_choices: gr.Markdown("<p style='color: red;'>Nenhum addon instalado suporta este modo.</p>")
            else:
                provider_choice_srt = gr.Radio(choices=srt_choices, value=srt_choices[0], label="Escolha o Provedor")
                srt_file_input = gr.File(label="Arquivo SRT", file_types=[".srt"])
                srt_uis, srt_inputs = {}, {}
                for name, addon in srt_addons.items():
                    with gr.Column(visible=(name == srt_choices[0])) as ui_wrapper:
                        ui_block, inputs = addon.create_srt_ui(); srt_uis[name], srt_inputs[name] = ui_wrapper, inputs
                audio_output_srt = gr.Audio(label="Resultado (apenas áudio)", type="filepath")
                gerar_srt_btn = gr.Button("Gerar Áudio do SRT", variant="primary")
                gr.Examples(examples=load_samples(), inputs=[srt_file_input], label="Exemplos")
                def switch_srt_ui(p_name): return {ui: gr.update(visible=(n == p_name)) for n, ui in srt_uis.items()}
                provider_choice_srt.change(fn=switch_srt_ui, inputs=provider_choice_srt, outputs=list(srt_uis.values()))
                def srt_dispatcher(p_name, f_obj, *args):
                    addon, s_idx = srt_addons[p_name], 0
                    for n, i in srt_inputs.items():
                        if n == p_name: return addon.process_srt(f_obj, *args[s_idx:s_idx+len(i)])
                        s_idx += len(i)
                all_srt_inputs = [i for n in srt_choices for i in srt_inputs[n]]
                gerar_srt_btn.click(fn=srt_dispatcher, inputs=[provider_choice_srt, srt_file_input] + all_srt_inputs, outputs=audio_output_srt, queue=True)

        with gr.TabItem("Gerenciar Addons"):
            gr.Markdown("## Instalar um novo Provedor de Voz")
            with gr.Tabs():
                with gr.TabItem("Instalar via Upload (.zip)"):
                    gr.Markdown("Faça o upload de um arquivo `.zip` contendo o addon.")
                    addon_zip_upload = gr.File(label="Arquivo .zip do Addon", file_types=[".zip"])
                    install_zip_button = gr.Button("Instalar Addon do ZIP", variant="primary")
                with gr.TabItem("Instalar via Git (Avançado)"):
                    gr.Markdown("Cole a URL de um repositório Git que contenha um addon compatível.", visible=GIT_AVAILABLE)
                    addon_repo_url = gr.Textbox(label="URL do Repositório Git", placeholder="https://github.com/usuario/meu-addon-tts.git", visible=GIT_AVAILABLE)
                    install_git_button = gr.Button("Instalar Addon do Git", visible=GIT_AVAILABLE)
                    if not GIT_AVAILABLE: gr.Markdown("`GitPython` não foi encontrado. A instalação via Git está desabilitada.")
            install_status = gr.Textbox(label="Status da Instalação", interactive=False)
            install_zip_button.click(fn=install_addon_from_zip, inputs=addon_zip_upload, outputs=install_status, queue=True)
            if GIT_AVAILABLE: install_git_button.click(fn=install_addon_from_git, inputs=addon_repo_url, outputs=install_status, queue=True)
            gr.Markdown("---"); gr.Markdown("### Addons Instalados Atualmente:")
            if loaded_addons: gr.HTML("<ul>" + "".join(f"<li>{name}</li>" for name in loaded_addons.keys()) + "</ul>")
            else: gr.Markdown("Nenhum addon carregado.")
                    
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
                &bull;
                <a href='https://github.com/open-mmlab/Amphion' target='_blank'>Amphion (Vevo)</a>
            </p>
        </div>
        """)

    iface.launch(share=True)