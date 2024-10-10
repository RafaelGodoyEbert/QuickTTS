# QuickTTS
TTS de maneira rápida com interface/UI utilizando EDGE-TTS<br>  <br> Este é um projeto que permite gerar áudio a partir de texto usando diferentes modelos de voz e velocidades de fala. Ele utiliza Edge-TTS (Gratuitamente). Além disso, oferece a opção de cortar o silêncio do áudio resultante. <br>

[![Discord](https://dcbadge.vercel.app/api/server/aihubbrasil)](https://discord.gg/aihubbrasil)
[![Open In Colab](https://img.shields.io/badge/Colab-F9AB00?style=for-the-badge&logo=googlecolab&color=525252)](https://colab.research.google.com/drive/1hpTDhlEEVZLtJ722d9U11DwNEadtxlu7?usp=sharing)
[![Huggingface](https://img.shields.io/badge/🤗%20-Spaces-yellow.svg?style=for-the-badge)](https://huggingface.co/spaces/RafaG/TTS-Rapido)

![quicktts](https://github.com/user-attachments/assets/72af9d64-4857-4eef-9a1b-59558804696d)

## Funcionalidades

- **Edge-TTS**: Utiliza a biblioteca Edge-TTS para gerar áudio a partir do texto inserido.

## Como usar
### Online
  No Colab, só dê play e seja feliz<br>
  No Huggingface o edge-tts também é tranquilo.

### Local
1. Clone o repositório para sua máquina local.
   ``git clone https://github.com/RafaelGodoyEbert/TTS-R-pido``
3. Instale as dependências necessárias especificadas no arquivo `requirements.txt`.
   ``pip install -r requirements.txt``
5. Execute o script Python `app.py`.
6. Acesse o aplicativo Gradio no navegador.
7. Ou execute o ``webui.bat``

## Dependências

- `gradio`: Para criar a interface de usuário interativa.
- `pydub`: Para manipular arquivos de áudio.
- `requests`: Para fazer solicitações HTTP à API Elevenlabs.

## Como contribuir

Se você deseja contribuir para este projeto, sinta-se à vontade para abrir uma [issue](https://github.com/RafaelGodoyEbert/TTS-R-pido/issues) ou enviar um [pull request](https://github.com/RafaelGodoyEbert/TTS-R-pido/pulls). Todas as contribuições são bem-vindas!

## Agradecimentos

- A [rany2](https://github.com/rany2) pelo Edge-TTS.
- Aos colaboradores deste projeto.

## Autor

Desenvolvido por Rafael Godoy Ebert.

Se gostou deste projeto e deseja apoiá-lo, considere [doar pelo Pix](https://nubank.com.br/pagar/1ls6a4/0QpSSbWBSq).
