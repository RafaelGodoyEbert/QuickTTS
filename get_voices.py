import subprocess
import asyncio
import json
from collections import defaultdict
from edge_tts import VoicesManager

# Dicionário para mapear códigos de idioma para nomes completos
language_mapping = {
    "af": "Afrikaans",
    "am": "Amharic",
    "ar": "Arabic",
    "az": "Azerbaijani",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "bs": "Bosnian",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "Deutsch",
    "al": "Albanian",
    "el": "Greek",
    "in": "Indonesian",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "fa": "Persian",
    "fi": "Finnish",
    "fil": "Filipino",
    "fr": "French",
    "ga": "Irish",
    "gl": "Galician",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "ja": "Japanese",
    "jv": "Javanese",
    "ka": "Georgian",
    "kk": "Kazakh",
    "km": "Khmer",
    "kn": "Kannada",
    "ko": "Korean",
    "lo": "Lao",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "mr": "Marathi",
    "ms": "Malay",
    "mt": "Maltese",
    "my": "Burmese",
    "nb": "Norwegian Bokmål",
    "ne": "Nepali",
    "nl": "Dutch",
    "pl": "Polish",
    "ps": "Pashto",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovenian",
    "so": "Somali",
    "sq": "Albanian",
    "sr": "Serbian",
    "su": "Sundanese",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "zh": "Chinese",
    "zu": "Zulu"
}

async def generate_voices_json():
    """
    Usa a biblioteca edge-tts para obter a lista de vozes diretamente,
    agrupa por nome de idioma mapeado e salva em voices.json.
    """
    print("Gerando lista de vozes a partir da API... Isso pode levar um momento.")
    
    try:
        voices_manager = await VoicesManager.create()
        voices_by_lang_name = defaultdict(list)
        
        for voice in voices_manager.voices:
            # Pega o código de localidade, ex: "pt-BR"
            locale_code = voice["Locale"]
            # Pega apenas a primeira parte (o código do idioma), ex: "pt"
            lang_code = locale_code.split('-')[0]
            
            # Usa o seu mapeamento para obter o nome completo, ex: "Portuguese"
            # Se o código não estiver no mapa, usa o próprio código como fallback
            language_name = language_mapping.get(lang_code, lang_code)
            
            voice_info = {
                "name": voice["ShortName"], 
                "gender": voice["Gender"]
            }
            
            voices_by_lang_name[language_name].append(voice_info)

        # Ordena o dicionário final pelo nome do idioma para consistência
        sorted_voices = dict(sorted(voices_by_lang_name.items()))

        with open("voices.json", "w", encoding="utf-8") as f:
            json.dump(sorted_voices, f, ensure_ascii=False, indent=4)
            
        print(f"Lista de vozes salva com sucesso em 'voices.json'.")
        print(f"Total de {len(voices_manager.voices)} vozes em {len(sorted_voices)} idiomas.")

    except Exception as e:
        print(f"Ocorreu um erro ao tentar gerar o arquivo de vozes: {e}")
        print("Verifique sua conexão com a internet e se a biblioteca 'edge-tts' está instalada corretamente.")

# A função 'get_voices' agora é um simples wrapper para a função assíncrona
def get_voices():
    """Wrapper síncrono para executar a geração do JSON de vozes."""
    try:
        asyncio.run(generate_voices_json())
    except RuntimeError:
        # Lida com o caso de já haver um loop de eventos rodando (comum em notebooks)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(generate_voices_json())

if __name__ == "__main__":
    get_voices()