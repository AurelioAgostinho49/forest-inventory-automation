from rapidfuzz import process
from .normalizer import normalizar
from .base import ESPECIES
from .alias import ALIAS

def encontrar_especie(nome):
    nome_norm = normalizar(nome)

    if nome_norm in ALIAS:
        nome_norm = ALIAS[nome_norm]

    if not nome_norm:
        return None, None, None, 0

    match, score, _ = process.extractOne(
        nome_norm,
        ESPECIES.keys()
    )

    if not match:
        return None, None, None, score

    dados = ESPECIES[match]

    return match, dados["comum"], dados["cientifico"], score

def sugerir_especies(nome, limite=3):
    nome_norm = normalizar(nome)

    if nome_norm in ALIAS:
        nome_norm = ALIAS[nome_norm]

    return process.extract(
        nome_norm,
        ESPECIES.keys(),
        limit=limite
    )