from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import simplekml
from pyproj import Transformer


UTM_COORD_PATTERN = re.compile(
    r"(?<!\d)(\d{6,7}(?:[.,]0+)?)\s*/\s*(\d{7}(?:[.,]0+)?)(?!\d)"
)
TRANSFORMER_UTM_23S = Transformer.from_crs("EPSG:32723", "EPSG:4326", always_xy=True)
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "kml"


def _normalizar_string(valor: Any) -> str:
    if valor is None or pd.isna(valor):
        return ""

    texto = str(valor)
    texto = texto.replace("\xa0", " ")
    texto = texto.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _normalizar_texto_coordenada(valor: Any) -> str:
    texto = _normalizar_string(valor)
    if not texto:
        return ""

    texto = re.sub(r"(?i)\b(coord(?:enada)?s?)\b\s*[:=-]?\s*", "", texto)
    texto = re.sub(r"\s*/\s*", "/", texto)
    return texto.strip(" -;:,")


def _normalizar_componente_numerico(valor: str) -> int:
    texto = _normalizar_string(valor).replace(",", ".")
    numero = float(texto)

    if not numero.is_integer():
        raise ValueError("Os componentes UTM precisam ser números inteiros.")

    return int(numero)


def _formatar_coordenada(easting: int, northing: int) -> str:
    return f"{easting:07d}/{northing:07d}"


def _gerar_nome_arquivo(nome: str) -> str:
    nome_limpo = re.sub(r"[^A-Za-z0-9_-]+", "_", nome.strip()) or "Parcela"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{nome_limpo}_{timestamp}.kml"


def _indice_para_excel(indice: int) -> str:
    if indice < 0:
        return "?"

    resultado = ""
    atual = indice + 1

    while atual > 0:
        atual, resto = divmod(atual - 1, 26)
        resultado = chr(65 + resto) + resultado

    return resultado


def _rotulo_coluna(coluna: Any) -> str:
    if isinstance(coluna, int):
        return _indice_para_excel(coluna)

    texto = _normalizar_string(coluna)
    return texto or str(coluna)


def _iterar_candidatos_coordenada(df: pd.DataFrame, coluna: Any | None = None):
    colunas = [coluna] if coluna is not None else list(df.columns)

    for coluna_atual in colunas:
        cabecalho = _normalizar_texto_coordenada(coluna_atual)
        if cabecalho:
            yield {
                "coluna": coluna_atual,
                "origem": f"cabeçalho da coluna {_rotulo_coluna(coluna_atual)}",
                "coordenada_bruta": _normalizar_string(coluna_atual),
                "texto": cabecalho,
            }

    for linha_idx, (_, linha) in enumerate(df.iterrows(), start=1):
        for coluna_atual in colunas:
            valor = linha[coluna_atual]
            texto = _normalizar_texto_coordenada(valor)
            if not texto:
                continue

            yield {
                "coluna": coluna_atual,
                "origem": f"célula {_indice_para_excel(df.columns.get_loc(coluna_atual))}{linha_idx}",
                "coordenada_bruta": _normalizar_string(valor),
                "texto": texto,
            }


def _detectar_primeira_coordenada(df: pd.DataFrame, coluna: Any | None = None) -> dict[str, Any] | None:
    for candidato in _iterar_candidatos_coordenada(df, coluna=coluna):
        if UTM_COORD_PATTERN.search(candidato["texto"]):
            return candidato

    return None


def detectar_coluna_coordenada(df: pd.DataFrame) -> Any | None:
    try:
        if df is None or df.empty:
            return None

        contagens: dict[Any, int] = {coluna: 0 for coluna in df.columns}

        for candidato in _iterar_candidatos_coordenada(df):
            if UTM_COORD_PATTERN.search(candidato["texto"]):
                contagens[candidato["coluna"]] += 1

        if not any(contagens.values()):
            return None

        return max(contagens, key=contagens.get)

    except Exception:
        return None


def extrair_coordenada(df: pd.DataFrame, coluna: Any) -> str | None:
    try:
        if df is None or df.empty or coluna not in df.columns:
            return None

        candidato = _detectar_primeira_coordenada(df, coluna=coluna)
        if not candidato:
            return None

        easting, northing = parse_utm(candidato["texto"])
        return _formatar_coordenada(easting, northing)

    except Exception:
        return None


def parse_utm(coord_str: str) -> tuple[int, int]:
    try:
        texto = _normalizar_texto_coordenada(coord_str)
        match = UTM_COORD_PATTERN.search(texto)

        if not match:
            raise ValueError("Coordenada UTM inválida. Use o padrão 0605267/8135103.")

        easting = _normalizar_componente_numerico(match.group(1))
        northing = _normalizar_componente_numerico(match.group(2))
        return easting, northing

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Não foi possível interpretar a coordenada UTM.") from exc


def utm_para_latlon(easting: int, northing: int) -> tuple[float, float]:
    try:
        if not isinstance(easting, int) or not isinstance(northing, int):
            raise ValueError("Easting e Northing precisam ser inteiros.")

        lon, lat = TRANSFORMER_UTM_23S.transform(easting, northing)

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("A conversão UTM gerou latitude/longitude fora da faixa esperada.")

        return lat, lon

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Erro ao converter coordenada UTM para latitude/longitude.") from exc


def gerar_kml(lat: float, lon: float, nome: str = "Parcela") -> str:
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        caminho_arquivo = OUTPUT_DIR / _gerar_nome_arquivo(nome)

        kml = simplekml.Kml()
        ponto = kml.newpoint(name=nome, coords=[(lon, lat)])
        ponto.description = f"Latitude: {lat:.6f}, Longitude: {lon:.6f}"
        kml.save(str(caminho_arquivo))

        return str(caminho_arquivo)

    except Exception as exc:
        raise ValueError("Erro ao gerar o arquivo KML.") from exc


def processar_coordenada_auto(df: pd.DataFrame) -> dict[str, Any]:
    try:
        if df is None or df.empty:
            raise ValueError("A planilha está vazia e não possui coordenadas para processar.")

        coluna = detectar_coluna_coordenada(df)
        if coluna is None:
            raise ValueError("Nenhuma coordenada UTM foi detectada na aba.")

        erros: list[str] = []

        for candidato in _iterar_candidatos_coordenada(df, coluna=coluna):
            match = UTM_COORD_PATTERN.search(candidato["texto"])
            if not match:
                continue

            coordenada_bruta = candidato["coordenada_bruta"]

            try:
                easting, northing = parse_utm(candidato["texto"])
                coordenada = _formatar_coordenada(easting, northing)
                lat, lon = utm_para_latlon(easting, northing)
            except ValueError as exc:
                erros.append(f"{candidato['origem']} ({coordenada_bruta}): {exc}")
                continue

            nome_ponto = "Parcela"
            if "Parcela" in df.columns:
                parcelas = df["Parcela"].dropna()
                if not parcelas.empty:
                    nome_ponto = f"Parcela {parcelas.iloc[0]}"

            caminho_kml = gerar_kml(lat, lon, nome=nome_ponto)

            return {
                "coluna": _rotulo_coluna(coluna),
                "origem": candidato["origem"],
                "coordenada_bruta": coordenada_bruta,
                "coordenada": coordenada,
                "easting": easting,
                "northing": northing,
                "latitude": lat,
                "longitude": lon,
                "arquivo_kml": caminho_kml,
                "nome_ponto": nome_ponto,
            }

        if erros:
            raise ValueError("Coordenadas detectadas, mas rejeitadas: " + " | ".join(erros))

        raise ValueError(f"Nenhuma coordenada UTM válida foi encontrada na coluna '{_rotulo_coluna(coluna)}'.")

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Não foi possível processar a coordenada automaticamente.") from exc


def processar_coordenada_arquivo_excel(arquivo: BytesIO) -> dict[str, Any]:
    try:
        xls = pd.ExcelFile(arquivo)
        erros_por_aba: list[str] = []

        for aba in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=aba, header=None)
            if df.empty:
                erros_por_aba.append(f"{aba}: aba vazia.")
                continue

            try:
                resultado = processar_coordenada_auto(df)
                resultado["aba"] = aba
                return resultado
            except ValueError as exc:
                erros_por_aba.append(f"{aba}: {exc}")

        detalhes = " ".join(erros_por_aba) if erros_por_aba else "Nenhuma aba foi lida."
        raise ValueError(f"Nenhuma coordenada UTM válida foi encontrada na planilha. Detalhes: {detalhes}")

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Erro ao analisar o arquivo Excel para geração do KML.") from exc
