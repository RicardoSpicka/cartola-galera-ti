
import csv
import time
from pathlib import Path

import requests


BASE_URL = "https://api.cartolafc.globo.com"
RODADA_INICIAL = 19
ARQUIVO = Path(__file__).resolve().parent / "historico_cartola.csv"
TIMEOUT = 30
TENTATIVAS = 3

TIMES = [
    {"id": 48959555, "nome_time": "Pácábá Sporte Club", "cartoleiro": "Ricardo Spicka"},
    {"id": 51313999, "nome_time": "kopo d'água", "cartoleiro": "Miriam"},
    {"id": 51242673, "nome_time": "divadafiel", "cartoleiro": "debz"},
    {"id": 51313793, "nome_time": "AIMS Acaba", "cartoleiro": "Vicente"},
    {"id": 28884151, "nome_time": "cBenefs", "cartoleiro": "Bruno H Favoreto"},
    {"id": 51313791, "nome_time": "FEBRE DO RATO DE ESGOTO", "cartoleiro": "Raquel Silva"},
]

# Estes nomes correspondem ao dashboard.py atual.
CAMPOS = [
    "rodada",
    "time_id",
    "nome_time",
    "cartoleiro",
    "pontos_rodada",
    "pontos_acumulados_liga",
    "patrimonio",
    "posicao_liga",
    "status",
]


def consultar_api(url):
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
                raise ValueError("Resposta inesperada da API.")

            return dados

        except (requests.RequestException, ValueError) as erro:
            ultimo_erro = erro
            print(f"Tentativa {tentativa}/{TENTATIVAS}: {erro}")

            if tentativa < TENTATIVAS:
                time.sleep(2 * tentativa)

    raise RuntimeError(f"Falha ao consultar {url}") from ultimo_erro


def obter_ultima_rodada_salva():
    if not ARQUIVO.exists():
        return RODADA_INICIAL - 1

    with ARQUIVO.open("r", newline="", encoding="utf-8-sig") as arquivo:
        leitor = csv.DictReader(arquivo)

        if "rodada" not in (leitor.fieldnames or []):
            raise RuntimeError("O CSV atual não possui a coluna rodada.")

        rodadas = [
            int(linha["rodada"])
            for linha in leitor
            if linha.get("rodada")
        ]

    return max(rodadas, default=RODADA_INICIAL - 1)


def obter_dados_time(time_info, rodada):
    url = f"{BASE_URL}/time/id/{time_info['id']}/{rodada}"
    dados = consultar_api(url)

    pontos = dados.get("pontos")
    patrimonio = dados.get("patrimonio")

    if pontos is None or patrimonio is None:
        raise RuntimeError(
            f"Dados incompletos: {time_info['nome_time']}, rodada {rodada}."
        )

    return float(pontos), float(patrimonio)


def coletar_historico():
    print("Iniciando atualização do histórico da Liga Galera TI.")

    status = consultar_api(f"{BASE_URL}/mercado/status")
    rodada_atual = status.get("rodada_atual")

    if not isinstance(rodada_atual, int) or rodada_atual < 1:
        raise RuntimeError("A API não informou uma rodada válida.")

    ultima_salva = obter_ultima_rodada_salva()

    # Considera concluída a rodada anterior à rodada atual da API.
    # Nunca reduz a quantidade de rodadas que já existe no CSV.
    rodada_final = max(ultima_salva, rodada_atual - 1)

    if rodada_final < RODADA_INICIAL:
        raise RuntimeError("Não há rodadas disponíveis para coletar.")

    print(f"Rodada informada pela API: {rodada_atual}")
    print(f"Histórico será reconstruído até a rodada {rodada_final}.")

    linhas = []
    acumulados = {time["id"]: 0.0 for time in TIMES}

    for rodada in range(RODADA_INICIAL, rodada_final + 1):
        print(f"\nColetando rodada {rodada}...")
        dados_rodada = []

        for time_info in TIMES:
            pontos, patrimonio = obter_dados_time(time_info, rodada)
            acumulados[time_info["id"]] += pontos

            dados_rodada.append({
                "rodada": rodada,
                "time_id": str(time_info["id"]),
                "nome_time": time_info["nome_time"],
                "cartoleiro": time_info["cartoleiro"],
                "pontos_rodada": pontos,
                "pontos_acumulados_liga": round(
                    acumulados[time_info["id"]], 2
                ),
                "patrimonio": patrimonio,
                "posicao_liga": 0,
                "status": "OK",
            })

            print(f"  {time_info['nome_time']}: {pontos:.2f} pontos")
            time.sleep(0.2)

        # Classificação acumulada da liga até esta rodada.
        classificacao = sorted(
            dados_rodada,
            key=lambda item: item["pontos_acumulados_liga"],
            reverse=True,
        )

        for posicao, item in enumerate(classificacao, start=1):
            item["posicao_liga"] = posicao

        linhas.extend(dados_rodada)

    validar_historico(linhas, rodada_final)
    salvar_historico(linhas)

    print("\nHistórico atualizado com sucesso.")
    print(f"Total de registros: {len(linhas)}")


def validar_historico(linhas, rodada_final):
    esperado = (rodada_final - RODADA_INICIAL + 1) * len(TIMES)

    if len(linhas) != esperado:
        raise RuntimeError(
            f"Esperados {esperado} registros; recebidos {len(linhas)}."
        )

    for rodada in range(RODADA_INICIAL, rodada_final + 1):
        registros = [linha for linha in linhas if linha["rodada"] == rodada]
        ids = {linha["time_id"] for linha in registros}

        if len(registros) != len(TIMES) or len(ids) != len(TIMES):
            raise RuntimeError(
                f"A rodada {rodada} não contém exatamente os seis times."
            )

        for linha in registros:
            if not linha["nome_time"] or not linha["cartoleiro"]:
                raise RuntimeError(f"Identificação incompleta na rodada {rodada}.")

    print("Validação dos dados concluída.")


def salvar_historico(linhas):
    temporario = ARQUIVO.with_suffix(".tmp")

    try:
        with temporario.open("w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS)
            escritor.writeheader()
            escritor.writerows(linhas)

        # Só substitui o CSV atual após a coleta e validação completas.
        temporario.replace(ARQUIVO)

    finally:
        if temporario.exists():
            temporario.unlink()


if __name__ == "__main__":
    coletar_historico()
