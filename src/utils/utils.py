from deep_translator import GoogleTranslator
from src.core.constants import LANGUAGES
import logging

def translate_text(text, lang):
    """Translate text to the user's preferred language."""
    if lang == 'en':
        return text
    try:
        return GoogleTranslator(source='en', target=lang).translate(text)
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return text 