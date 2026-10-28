
import csv
import time
from pathlib import Path

import requests


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_URL = "https://api.cartolafc.globo.com"

RODADA_INICIAL = 19

ARQUIVO_HISTORICO = Path(__file__).parent / "historico_cartola.csv"

TIMEOUT = 30
TENTATIVAS = 3

TIMES = [
    {
        "id": 48959555,
        "nome": "Pácábá Sporte Club",
        "cartoleiro": "Ricardo Spicka",
    },
    {
        "id": 51313999,
        "nome": "kopo d'água",
        "cartoleiro": "Miriam",
    },
    {
        "id": 51242673,
        "nome": "divadafiel",
        "cartoleiro": "debz",
    },
    {
        "id": 51313793,
        "nome": "AIMS Acaba",
        "cartoleiro": "Vicente",
    },
    {
        "id": 28884151,
        "nome": "cBenefs",
        "cartoleiro": "Bruno H Favoreto",
    },
    {
        "id": 51313791,
        "nome": "FEBRE DO RATO DE ESGOTO",
        "cartoleiro": "Raquel Silva",
    },
]

CAMPOS_CSV = [
    "rodada",
    "time_id",
    "time",
    "cartoleiro",
    "pontos",
    "patrimonio",
    "pontos_acumulados",
    "posicao_rodada",
    "posicao_geral",
]


# ============================================================
# CONSULTAS À API
# ============================================================

def consultar_api(url):
    """Consulta a API com tentativas em caso de falha."""

    ultimo_erro = None

    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = requests.get(
                url,
                timeout=TIMEOUT,
                headers={
                    "User-Agent": "Mozilla/5.0 CartolaLigaGaleraTI/1.0"
                },
            )

            resposta.raise_for_status()

            dados = resposta.json()

            if not isinstance(dados, dict):
                raise ValueError("A API retornou um formato inesperado.")

            return dados

        except (requests.RequestException, ValueError) as erro:
            ultimo_erro = erro

            print(
                f"Falha na consulta ({tentativa}/{TENTATIVAS}): "
                f"{url} - {erro}"
            )

            if tentativa < TENTATIVAS:
                time.sleep(2 * tentativa)

    raise RuntimeError(
        f"Não foi possível consultar a API: {url}"
    ) from ultimo_erro


def obter_rodada_atual():
    """Obtém a rodada informada pela API do Cartola."""

    dados = consultar_api(f"{BASE_URL}/mercado/status")

    rodada = dados.get("rodada_atual")

    if not isinstance(rodada, int) or rodada < 1:
        raise RuntimeError(
            "A API não retornou uma rodada atual válida."
        )

    return rodada


def obter_dados_time(time_info, rodada):
    """Consulta a pontuação e o patrimônio de um time em uma rodada."""

    url = (
        f"{BASE_URL}/time/id/"
        f"{time_info['id']}/{rodada}"
    )

    dados = consultar_api(url)

    pontos = dados.get("pontos")
    patrimonio = dados.get("patrimonio")

    if pontos is None or patrimonio is None:
        raise RuntimeError(
            f"Dados incompletos para "
            f"{time_info['nome']} na rodada {rodada}."
        )

    return {
        "pontos": float(pontos),
        "patrimonio": float(patrimonio),
    }


# ============================================================
# LEITURA DO HISTÓRICO EXISTENTE
# ============================================================

def obter_ultima_rodada_salva():
    """Descobre a última rodada já existente no CSV."""

    if not ARQUIVO_HISTORICO.exists():
        return RODADA_INICIAL - 1

    with ARQUIVO_HISTORICO.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as arquivo:
        leitor = csv.DictReader(arquivo)

        if "rodada" not in (leitor.fieldnames or []):
            raise RuntimeError(
                "O CSV existente não possui a coluna 'rodada'."
            )

        rodadas = []

        for linha in leitor:
            valor = linha.get("rodada")

            if valor:
                rodadas.append(int(valor))

    return max(rodadas, default=RODADA_INICIAL - 1)


# ============================================================
# COLETA DO HISTÓRICO
# ============================================================

def coletar_historico():
    print("=" * 60)
    print("ATUALIZAÇÃO DO HISTÓRICO - LIGA GALERA TI")
    print("=" * 60)

    rodada_atual = obter_rodada_atual()
    ultima_rodada_salva = obter_ultima_rodada_salva()

    # Não reduz o histórico já publicado.
    rodada_final = max(
        ultima_rodada_salva,
        rodada_atual - 1,
    )

    print(f"Rodada informada pela API: {rodada_atual}")
    print(f"Última rodada salva: {ultima_rodada_salva}")
    print(f"Rodada final da coleta: {rodada_final}")

    if rodada_final < RODADA_INICIAL:
        raise RuntimeError(
            "Ainda não há rodadas disponíveis para coletar."
        )

    linhas = []
    pontos_acumulados = {
        time_info["id"]: 0.0
        for time_info in TIMES
    }

    # Coleta todas as rodadas para reconstruir o CSV completo.
    # O arquivo original só será substituído após validar tudo.
    for rodada in range(RODADA_INICIAL, rodada_final + 1):
        print(f"\nColetando rodada {rodada}...")

        dados_rodada = []

        for time_info in TIMES:
            dados_time = obter_dados_time(time_info, rodada)

            pontos_acumulados[time_info["id"]] += (
                dados_time["pontos"]
            )

            dados_rodada.append({
                "rodada": rodada,
                "time_id": time_info["id"],
                "time": time_info["nome"],
                "cartoleiro": time_info["cartoleiro"],
                "pontos": dados_time["pontos"],
                "patrimonio": dados_time["patrimonio"],
                "pontos_acumulados": pontos_acumulados[
                    time_info["id"]
                ],
            })

            print(
                f"  {time_info['nome']}: "
                f"{dados_time['pontos']:.2f} pontos"
            )

            time.sleep(0.2)

        # Classifica os times da rodada pela pontuação.
        classificacao_rodada = sorted(
            dados_rodada,
            key=lambda item: item["pontos"],
            reverse=True,
        )

        for posicao, item in enumerate(
            classificacao_rodada,
            start=1,
        ):
            item["posicao_rodada"] = posicao

        # Classificação geral pelo acumulado até a rodada.
        classificacao_geral = sorted(
            dados_rodada,
            key=lambda item: item["pontos_acumulados"],
            reverse=True,
        )

        for posicao, item in enumerate(
            classificacao_geral,
            start=1,
        ):
            item["posicao_geral"] = posicao

        linhas.extend(dados_rodada)

    validar_historico(linhas, rodada_final)

    salvar_historico(linhas)

    print("\n" + "=" * 60)
    print(f"Histórico atualizado: {ARQUIVO_HISTORICO}")
    print(f"Total de registros: {len(linhas)}")
    print(f"Rodadas processadas: {RODADA_INICIAL} a {rodada_final}")
    print("=" * 60)


# ============================================================
# VALIDAÇÃO E GRAVAÇÃO SEGURA
# ============================================================

def validar_historico(linhas, rodada_final):
    """Valida a coleta antes de substituir o CSV existente."""

    quantidade_rodadas = rodada_final - RODADA_INICIAL + 1
    quantidade_esperada = quantidade_rodadas * len(TIMES)

    if len(linhas) != quantidade_esperada:
        raise RuntimeError(
            f"Quantidade incorreta de registros: "
            f"{len(linhas)}; esperado: {quantidade_esperada}."
        )

    for rodada in range(RODADA_INICIAL, rodada_final + 1):
        registros = [
            item for item in linhas
            if item["rodada"] == rodada
        ]

        if len(registros) != len(TIMES):
            raise RuntimeError(
                f"A rodada {rodada} não contém todos os times."
            )

        ids = {item["time_id"] for item in registros}

        if len(ids) != len(TIMES):
            raise RuntimeError(
                f"Existem times duplicados na rodada {rodada}."
            )

    print("\nValidação concluída com sucesso.")


def salvar_historico(linhas):
    """Grava primeiro em arquivo temporário e só depois substitui o CSV."""

    arquivo_temporario = ARQUIVO_HISTORICO.with_suffix(".tmp")

    try:
        with arquivo_temporario.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as arquivo:
            escritor = csv.DictWriter(
                arquivo,
                fieldnames=CAMPOS_CSV,
                delimiter=",",
            )

            escritor.writeheader()
            escritor.writerows(linhas)

        # Substitui o arquivo original somente após a gravação completa.
        arquivo_temporario.replace(ARQUIVO_HISTORICO)

    finally:
        if arquivo_temporario.exists():
            arquivo_temporario.unlink()


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    coletar_historico()
