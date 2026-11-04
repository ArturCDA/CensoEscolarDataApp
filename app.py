
import json
from pathlib import Path

import pandas as pd


# Caminhos do projeto
BASE_DIR = Path(__file__).resolve().parent
DADOS_DIR = BASE_DIR / "dados"
RESULTADO_DIR = BASE_DIR / "resultado"

# Arquivos de entrada
ARQUIVO_ESCOLAS = DADOS_DIR / "Tabela_Escola_2025_V2.csv"
ARQUIVO_MATRICULAS = DADOS_DIR / "Tabela_Matricula_2025_V2.csv"

# Arquivo de saída
ARQUIVO_JSON = RESULTADO_DIR / "instituicoes_pb_2025.json"


def ler_csv(caminho):
    """Lê os microdados do INEP."""
    return pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        low_memory=False
    )


def main():
    # 1. Ler as tabelas
    escolas = ler_csv(ARQUIVO_ESCOLAS)
    matriculas = ler_csv(ARQUIVO_MATRICULAS)

    # 2. Filtrar as escolas da Paraíba
    # CO_UF da Paraíba = 25
    escolas = escolas[
        escolas["CO_UF"] == 25
    ].copy()

    # 3. Somar as matrículas por instituição
    # Ajuste os nomes das colunas conforme o dicionário.
    colunas_matricula = {
        "QT_MAT_BAS": "qt_mat_bas",
        "QT_MAT_INF": "qt_mat_inf",
        "QT_MAT_FUND": "qt_mat_fund",
        "QT_MAT_MED": "qt_mat_med",
        "QT_MAT_PROF": "qt_mat_prof",
        "QT_MAT_EJA": "qt_mat_eja",
        "QT_MAT_ESP": "qt_mat_esp",
    }

    matriculas = matriculas.rename(
        columns=colunas_matricula
    )

    colunas_quantidade = list(
        colunas_matricula.values()
    )

    # Garantir que os valores sejam numéricos
    for coluna in colunas_quantidade:
        matriculas[coluna] = pd.to_numeric(
            matriculas[coluna],
            errors="coerce"
        ).fillna(0)

    # Agrupar pelo código da instituição
    matriculas_agrupadas = (
        matriculas
        .groupby("CO_ENTIDADE")[colunas_quantidade]
        .sum()
        .reset_index()
    )

    # 4. Relacionar escolas e matrículas
    dados = escolas.merge(
        matriculas_agrupadas,
        on="CO_ENTIDADE",
        how="left"
    )

    # 5. Preencher matrículas ausentes com zero
    dados[colunas_quantidade] = (
        dados[colunas_quantidade]
        .fillna(0)
        .astype(int)
    )

    # 6. Selecionar os campos solicitados
    campos = [
        "NO_ENTIDADE",
        "CO_ENTIDADE",
        "NO_UF",
        "SG_UF",
        "CO_UF",
        "NO_MUNICIPIO",
        "CO_MUNICIPIO",
        "NO_MESORREGIAO",
        "CO_MESORREGIAO",
        "NO_MICRORREGIAO",
        "CO_MICRORREGIAO",
        "NU_ANO_CENSO",
        "NO_REGIAO",
        "CO_REGIAO",
        "qt_mat_bas",
        "qt_mat_inf",
        "qt_mat_fund",
        "qt_mat_med",
        "qt_mat_prof",
        "qt_mat_eja",
        "qt_mat_esp",
    ]

    # Criar colunas geográficas caso não existam
    colunas_geograficas = [
        "NO_MESORREGIAO",
        "CO_MESORREGIAO",
        "NO_MICRORREGIAO",
        "CO_MICRORREGIAO",
    ]

    for coluna in colunas_geograficas:
        if coluna not in dados.columns:
            dados[coluna] = None

    # 7. Renomear os campos cadastrais
    dados = dados.rename(columns={
        "NO_ENTIDADE": "no_entidade",
        "CO_ENTIDADE": "co_entidade",
        "NO_UF": "no_uf",
        "SG_UF": "sg_uf",
        "CO_UF": "co_uf",
        "NO_MUNICIPIO": "no_municipio",
        "CO_MUNICIPIO": "co_municipio",
        "NO_MESORREGIAO": "no_mesorregiao",
        "CO_MESORREGIAO": "co_mesorregiao",
        "NO_MICRORREGIAO": "no_microrregiao",
        "CO_MICRORREGIAO": "co_microrregiao",
        "NU_ANO_CENSO": "nu_ano_censo",
        "NO_REGIAO": "no_regiao",
        "CO_REGIAO": "co_regiao",
    })

    # 8. Exportar o JSON
    campos_json = [
        campo.lower() for campo in campos
    ]

    dados = dados.rename(columns={
        campo: campo.lower()
        for campo in campos
    })

    dados = dados[campos_json]

    RESULTADO_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    dados.to_json(
        ARQUIVO_JSON,
        orient="records",
        force_ascii=False,
        indent=4
    )

    print(f"Total de instituições: {len(dados)}")
    print(f"Arquivo gerado: {ARQUIVO_JSON}")


if __name__ == "__main__":
    main()
