import unicodedata
import re

def normalizar(texto):
    if not isinstance(texto, str):
        return ""

    texto = texto.lower()

    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))

    texto = texto.replace("-", " ")

    texto = re.sub(r'[^a-z\s]', '', texto)

    texto = " ".join(texto.split())

    return texto