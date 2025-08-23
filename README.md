# QuickTTS 🎙️

**QuickTTS** é uma ferramenta de Texto-para-Fala (TTS) poderosa e versátil, construída com uma interface Gradio limpa e intuitiva. Atendendo a pedidos da comunidade, este projeto foi desenvolvido para ser uma solução completa para geração de áudio, dublagem e muito mais.

[![Discord](https://dcbadge.vercel.app/api/server/aihubbrasil)](https://discord.gg/tAdPHFAbud)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1XtHdHqnMxjuuXPZkhpCLJIweV09n7YJF?usp=sharing)
[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20-Hugging%20Face-yellow.svg)](https://huggingface.co/spaces/RafaG/TTS-Rapido)

---

![Visão Geral do QuickTTS](https://github.com/user-attachments/assets/72af9d64-4857-4eef-9a1b-59558804696d)
*Interface principal mostrando a seleção de provedores e as opções de áudio.*

## ✨ Funcionalidades Principais

QuickTTS vai além da simples geração de áudio, oferecendo um conjunto de ferramentas robusto para diversas necessidades:

- **Múltiplos Provedores de TTS**: Escolha entre a vasta gama de vozes de alta qualidade do **Edge-TTS** ou as populares e virais vozes do **TikTok TTS**.
- **Suporte Global**: Gere áudio em dezenas de idiomas e dialetos, com centenas de vozes masculinas e femininas para escolher.
- **Sincronização de Legendas (.SRT)**: Carregue um arquivo de legenda (`.srt`) e gere automaticamente um arquivo de áudio perfeitamente sincronizado, ideal para dublagens de vídeos, cursos e outros projetos.
- **Processamento em Lote**: Converta o conteúdo de arquivos de texto (`.txt`) inteiros em um único arquivo de áudio com facilidade.
- **Ajustes Finos de Áudio**: Controle a **velocidade**, o **tom** e o **volume** do áudio gerado pelo Edge-TTS.
- **Remoção Inteligente de Silêncio**: Opcionalmente, remova pausas e silêncios indesejados do áudio final para um resultado mais dinâmico.
- **Exemplos Integrados**: Comece rapidamente com exemplos de SRT pré-configurados para testar a funcionalidade de dublagem com um único clique.
- **Interface em Tempo Real**: Acompanhe o progresso do processamento de arquivos SRT com uma barra de progresso interativa diretamente na interface.

## 🚀 Como Usar

Você pode usar o QuickTTS de três maneiras fáceis, sem precisar instalar nada localmente se não quiser.

### 1. Hugging Face Spaces (Recomendado para Edge-TTS)
Acesse a versão pública e sempre disponível diretamente no seu navegador. Ideal para testar rapidamente as funcionalidades do Edge-TTS.
- **[Acessar QuickTTS no Hugging Face](https://huggingface.co/spaces/RafaG/TTS-Rapido)**
  > **Nota:** A funcionalidade do TikTok TTS é bloqueada no Hugging Face devido a restrições de rede.

### 2. Google Colab (Recomendado para TikTok TTS)
Para usar todas as funcionalidades, incluindo o TikTok TTS, o Google Colab é a melhor opção online.
- **[Abrir no Google Colab](https://colab.research.google.com/drive/1hpTDhlEEVZLtJ722d9U11DwNEadtxlu7?usp=sharing)**
  - Basta clicar no link, e depois em "Executar tudo" (ou executar as células uma por uma). Um link público será gerado para você acessar a interface.

### 3. Execução Local (Controle Total)
Para a melhor performance e uso offline, clone e execute o projeto na sua própria máquina.

1.  **Pré-requisitos:**
    - Python 3.9+
    - FFmpeg (essencial para manipulação de áudio). [Instruções de instalação aqui](https://ffmpeg.org/download.html).

2.  **Clone o repositório:**
    ```bash
    git clone https://github.com/RafaelGodoyEbert/QuickTTS.git
    cd QuickTTS
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute o aplicativo:**
    ```bash
    python app.py
    ```
    - Ou, no Windows, simplesmente execute o arquivo `webui.bat`.

5.  Acesse o aplicativo no seu navegador através da URL local fornecida (geralmente `http://127.0.0.1:7860`).

## 🤝 Como Contribuir

Contribuições são sempre bem-vindas! Se você tem uma ideia para uma nova funcionalidade, encontrou um bug ou quer melhorar o código, sinta-se à vontade para:
- Abrir uma [Issue](https://github.com/RafaelGodoyEbert/QuickTTS/issues) para discutir sua ideia.
- Enviar um [Pull Request](https://github.com/RafaelGodoyEbert/QuickTTS/pulls) com suas melhorias.

## 🙏 Agradecimentos

Este projeto só foi possível graças às excelentes bibliotecas de código aberto desenvolvidas pela comunidade:

- **[edge-tts](https://github.com/rany2/edge-tts)** por **rany2**
- **[TikTok-Voice-TTS](https://github.com/mark-rez/TikTok-Voice-TTS)** por **mark-rez**
- E, claro, à equipe do **[Gradio](https://gradio.app/)** por tornar a criação de interfaces de ML tão acessível.

## 👤 Autor

Desenvolvido com ❤️ por **Rafael Godoy Ebert**.

Se você gostou deste projeto e ele foi útil para você, considere apoiar meu trabalho. Qualquer valor ajuda a manter a motivação para criar e manter ferramentas como esta!

[**➡️ Apoiar via PIX (NuBank)**](https://nubank.com.br/pagar/1ls6a4/0QpSSbWBSq)

---
