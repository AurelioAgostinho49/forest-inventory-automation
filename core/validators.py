import pandas as pd

def limpar_linhas_vazias(df):
    return df.dropna(how="all")