import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)

import streamlit as st
from io import BytesIO
from services.excel_service import processar_arquivo

st.title("Inventário Florestal")

arquivo = st.file_uploader("Envie seu arquivo Excel", type=["xlsx"])

if arquivo:
    st.success("Arquivo carregado!")

    final, erros = processar_arquivo(arquivo)

    for aba, erro in erros:
        st.warning(f"Erro na aba {aba}: {erro}")

    if final is not None:
        output = BytesIO()
        final.to_excel(output, index=False)
        output.seek(0)

        st.success("Processamento concluído!")

        st.download_button(
            label="Baixar resultado",
            data=output,
            file_name="resultado.xlsx"
        )
    else:
        st.error("Nenhuma aba válida foi processada.")