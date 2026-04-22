import pandas as pd
from core.detector import identificar_colunas, identificar_nome_coluna
from core.transformations import calcular_cap, calcular_dap
from core.validators import limpar_linhas_vazias

def processar_aba(df, numero_parcela):
    df = limpar_linhas_vazias(df).copy()

    cap_col, alt_col = identificar_colunas(df)
    nome_col = identificar_nome_coluna(df)

    df['CAP'] = df[cap_col].apply(calcular_cap)
    df['Nome Comum'] = df[nome_col]
    df['Alt. Total'] = df[alt_col]

    df['DAP'] = df['CAP'].apply(calcular_dap)
    df['Parcela'] = numero_parcela
    df['Núm. Árvore'] = range(1, len(df) + 1)

    return df[["Parcela", "Núm. Árvore", "Nome Comum", "CAP", "DAP", "Alt. Total"]]


def processar_arquivo(arquivo):
    xls = pd.ExcelFile(arquivo)
    resultado = []
    erros = []

    for i, aba in enumerate(xls.sheet_names):
        df = pd.read_excel(xls, sheet_name=aba, header=None)

        if df.empty:
            continue

        try:
            df_proc = processar_aba(df, i + 1)
            resultado.append(df_proc)

        except Exception as e:
            erros.append((aba, str(e)))

    if resultado:
        final = pd.concat(resultado, ignore_index=True)
        return final, erros

    return None, erros
