import os
import sys
from io import BytesIO
from pathlib import Path

import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

from formatter import formatar_nome_cientifico, formatar_nome_comum
from services.coordenadas_service import processar_coordenada_arquivo_excel
from services.excel_service import processar_arquivo
from species.base import ESPECIES
from species.matcher import encontrar_especie, sugerir_especies
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
    arquivo_bytes = arquivo.getvalue()
    arquivo_token = f"{arquivo.name}:{len(arquivo_bytes)}"

    if st.session_state.get("arquivo_token") != arquivo_token:
        st.session_state["arquivo_token"] = arquivo_token
        st.session_state.pop("resultado_kml", None)

    st.success("Arquivo carregado!")

    final, erros = processar_arquivo(BytesIO(arquivo_bytes))

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
                sugestoes_formatadas = [sugestao[0] for sugestao in sugestoes]

                modo = st.radio(
                    f"Como corrigir '{nome_original}'?",
                    ["Selecionar sugestão", "Digitar nome comum", "Adicionar nova espécie"],
                    key=f"modo_{nome_original}",
                )

                if modo == "Selecionar sugestão":
                    escolha = st.selectbox(
                        "Sugestões",
                        options=[""] + sugestoes_formatadas,
                        key=f"select_{nome_original}",
                    )

                    if escolha:
                        correcoes[nome_original] = {
                            "tipo": "existente",
                            "chave": escolha,
                        }

                elif modo == "Digitar nome comum":
                    novo_nome = st.text_input(
                        "Novo nome comum",
                        key=f"input_comum_{nome_original}",
                    )

                    especie_base = st.selectbox(
                        "Associar à espécie:",
                        options=list(ESPECIES.keys()),
                        key=f"select_existente_{nome_original}",
                    )

                    if novo_nome and especie_base:
                        correcoes[nome_original] = {
                            "tipo": "alias",
                            "novo_nome": novo_nome,
                            "base": especie_base,
                        }

                elif modo == "Adicionar nova espécie":
                    novo_comum = st.text_input(
                        "Nome comum",
                        key=f"novo_comum_{nome_original}",
                    )

                    novo_cientifico = st.text_input(
                        "Nome científico",
                        key=f"novo_cientifico_{nome_original}",
                    )

                    if novo_comum and novo_cientifico:
                        correcoes[nome_original] = {
                            "tipo": "nova",
                            "comum": novo_comum,
                            "cientifico": novo_cientifico,
                        }

        if st.button("Aplicar correções"):
            for original, dados in correcoes.items():
                mask = final["Nome Comum"] == original

                if dados["tipo"] == "existente":
                    info = ESPECIES[dados["chave"]]
                elif dados["tipo"] == "alias":
                    info = ESPECIES[dados["base"]]
                else:
                    chave = normalizar(dados["comum"])
                    ESPECIES[chave] = {
                        "comum": formatar_nome_comum(dados["comum"]),
                        "cientifico": formatar_nome_cientifico(dados["cientifico"]),
                    }
                    info = ESPECIES[chave]

                final.loc[mask, "Nome Comum_processado"] = info["comum"]
                final.loc[mask, "Nome Científico"] = info["cientifico"]
                final.loc[mask, "score"] = 100

            st.success("Correções aplicadas!")

        output = BytesIO()
        final.to_excel(output, index=False)
        output.seek(0)

        st.success("Processamento concluído!")
        st.dataframe(final.head(20))

        st.download_button(
            label="Baixar resultado",
            data=output,
            file_name="resultado.xlsx",
        )
    else:
        st.error("Nenhuma aba válida foi processada.")

    st.subheader("Geoprocessamento")

    if st.button("Gerar KML"):
        try:
            resultado_kml = processar_coordenada_arquivo_excel(BytesIO(arquivo_bytes))
            st.session_state["resultado_kml"] = resultado_kml
            st.success(
                f"{resultado_kml['total_pontos']} coordenada(s) válida(s) incluída(s) no KML."
            )
        except ValueError as exc:
            st.session_state.pop("resultado_kml", None)
            st.error(str(exc))

    resultado_kml = st.session_state.get("resultado_kml")

    if resultado_kml:
        for ponto in resultado_kml["pontos"]:
            st.write(
                f"{ponto['nome_ponto']} ({ponto['aba']}): "
                f"{ponto['coordenada']} -> "
                f"{ponto['latitude']:.6f}, {ponto['longitude']:.6f}"
            )

        for parcela_invalida in resultado_kml["parcelas_invalidas"]:
            st.warning(
                f"A coordenada da parcela {parcela_invalida['parcela']} "
                f"({parcela_invalida['aba']}) está inválida e não foi incluída no KML. "
                f"Motivo: {parcela_invalida['motivo']}"
            )

        caminho_kml = Path(resultado_kml["arquivo_kml"])
        if caminho_kml.exists():
            with open(caminho_kml, "rb") as arquivo_kml:
                st.download_button(
                    label="Baixar KML",
                    data=arquivo_kml.read(),
                    file_name=caminho_kml.name,
                    mime="application/vnd.google-earth.kml+xml",
                )
