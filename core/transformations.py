import math
import pandas as pd

def calcular_cap(valor):
    try:
        if pd.isna(valor):
            return None

        if isinstance(valor, str):
            valor = valor.replace('-', ',')
            partes = valor.split(',')

            numeros = [float(p) for p in partes if p.strip() != '']
            return math.sqrt(sum(n**2 for n in numeros))

        return float(valor)

    except:

        return None

def calcular_dap(cap):
    
    if cap is None:
        return None
    
    return cap / math.pi