import pandas as pd

def identificar_nome_coluna(df):
    scores = {}

    for col in df.columns:
        valores = df[col].astype(str)

        text_count = valores.apply(lambda x: any(c.isalpha() for c in x)).sum()

        scores[col] = text_count
        nome_col = max(scores, key=scores.get)

        return nome_col

def identificar_colunas(df):
    
    df_temp = df.copy()

    for col in df_temp.columns:
        df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce')

    colunas_numericas = df_temp.columns[df_temp.notna().sum() > 0] #É necessário que haja ao menos um valor numérico, mas o que acontece se todos os indivíduos tiverem bifurcações?

    if len(colunas_numericas) < 2:
        raise ValueError("Não foi possível identificar CAP e ALTURA")

    medias = {}

    for col in colunas_numericas:
        media = df_temp[col].mean()
        if pd.notna(media):
            medias[col] = media

    if len(medias) < 2:
        raise ValueError("Dados insuficientes para identificar colunas")

    cap_col = max(medias, key=medias.get)
    alt_col = min(medias, key=medias.get)

    return cap_col, alt_col