import subprocess
import json
import re
from collections import defaultdict

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

def get_voices():
    # Executa o comando edge-tts --list-voices
    result = subprocess.run(['edge-tts', '--list-voices'], capture_output=True, text=True)

    if result.returncode != 0:
        print("Erro ao executar o comando edge-tts.")
        return

    # Processa a saída
    voices = result.stdout.strip().split("\n\n")
    voices_data = defaultdict(list)

    for voice in voices:
        # Usa regex para capturar o nome e o gênero
        match = re.findall(r'Name:\s*(.*?)\s*Gender:\s*(\w+)', voice)
        if match:
            name, gender = match[0]
            language_code = name.split('-')[0]  # Pega o código do idioma
            language_name = language_mapping.get(language_code, language_code)  # Obtém o nome completo do idioma
            voices_data[language_name].append({
                'name': name,
                'gender': gender
            })

    # Salva em um arquivo JSON
    with open('voices.json', 'w', encoding='utf-8') as json_file:
        json.dump(voices_data, json_file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    get_voices()
