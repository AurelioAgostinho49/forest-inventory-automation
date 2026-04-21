import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)

import streamlit as st
from io import BytesIO
from services.excel_service import processar_arquivo
from species.matcher import encontrar_especie, sugerir_especies
from species.base import ESPECIES
from formatter import formatar_nome_comum, formatar_nome_cientifico
from species.normalizer import normalizar


def processar_dataframe(df, coluna_nome):
    nomes_comuns = []
    nomes_cientificos = []
    scores = []

    for nome in df[coluna_nome]:
        match, comum, cientifico, score = encontrar_especie(nome)

        if score >= 80:
            nomes_comuns.append(comum)
            nomes_cientificos.append(cientifico)
        else:
            nomes_comuns.append(None)
            nomes_cientificos.append(None)

        scores.append(score)

    df["Nome Comum_processado"] = nomes_comuns
    df["Nome Científico"] = nomes_cientificos
    df["score"] = scores

    return df


st.title("Inventário Florestal")

arquivo = st.file_uploader("Envie seu arquivo Excel", type=["xlsx"])

if arquivo:
    st.success("Arquivo carregado!")

    final, erros = processar_arquivo(arquivo)

    for aba, erro in erros:
        st.warning(f"Erro na aba {aba}: {erro}")

    if final is not None:

        final = processar_dataframe(final, "Nome Comum")

        erros_df = final[final["score"] < 80]

        correcoes = {}

        if not erros_df.empty:
            st.warning("Espécies não reconhecidas:")

            erros_unicos = erros_df["Nome Comum"].dropna().unique()

            for nome_original in erros_unicos:
                st.write(f"Entrada: {nome_original}")

                sugestoes = sugerir_especies(nome_original)
                sugestoes_formatadas = [s[0] for s in sugestoes]

                modo = st.radio(
                    f"Como corrigir '{nome_original}'?",
                    ["Selecionar sugestão", "Digitar nome comum", "Adicionar nova espécie"],
                    key=f"modo_{nome_original}"
                )

                # 🔹 1. Selecionar sugestão
                if modo == "Selecionar sugestão":
                    escolha = st.selectbox(
                        "Sugestões",
                        options=[""] + sugestoes_formatadas,
                        key=f"select_{nome_original}"
                    )

                    if escolha:
                        correcoes[nome_original] = {
                            "tipo": "existente",
                            "chave": escolha
                        }

                # 🔹 2. Criar alias (novo nome comum → espécie existente)
                elif modo == "Digitar nome comum":
                    novo_nome = st.text_input(
                        "Novo nome comum",
                        key=f"input_comum_{nome_original}"
                    )

                    especie_base = st.selectbox(
                        "Associar à espécie:",
                        options=list(ESPECIES.keys()),
                        key=f"select_existente_{nome_original}"
                    )

                    if novo_nome and especie_base:
                        correcoes[nome_original] = {
                            "tipo": "alias",
                            "novo_nome": novo_nome,
                            "base": especie_base
                        }

                # 🔹 3. Nova espécie
                elif modo == "Adicionar nova espécie":
                    novo_comum = st.text_input(
                        "Nome comum",
                        key=f"novo_comum_{nome_original}"
                    )

                    novo_cientifico = st.text_input(
                        "Nome científico",
                        key=f"novo_cientifico_{nome_original}"
                    )

                    if novo_comum and novo_cientifico:
                        correcoes[nome_original] = {
                            "tipo": "nova",
                            "comum": novo_comum,
                            "cientifico": novo_cientifico
                        }

        # 🔥 BOTÃO DE APLICAÇÃO
        if st.button("Aplicar correções"):

            for original, dados in correcoes.items():
                mask = final["Nome Comum"] == original

                # 🔹 existente
                if dados["tipo"] == "existente":
                    info = ESPECIES[dados["chave"]]

                # 🔹 alias
                elif dados["tipo"] == "alias":
                    info = ESPECIES[dados["base"]]

                # 🔹 nova espécie
                elif dados["tipo"] == "nova":
                    chave = normalizar(dados["comum"])

                    ESPECIES[chave] = {
                        "comum": formatar_nome_comum(dados["comum"]),
                        "cientifico": formatar_nome_cientifico(dados["cientifico"])
                    }

                    info = ESPECIES[chave]

                final.loc[mask, "Nome Comum_processado"] = info["comum"]
                final.loc[mask, "Nome Científico"] = info["cientifico"]
                final.loc[mask, "score"] = 100

            st.success("Correções aplicadas!")

        # 🔥 OUTPUT
        output = BytesIO()
        final.to_excel(output, index=False)
        output.seek(0)

        st.success("Processamento concluído!")
        st.dataframe(final.head(20))

        st.download_button(
            label="Baixar resultado",
            data=output,
            file_name="resultado.xlsx"
        )

    else:
        st.error("Nenhuma aba válida foi processada.")