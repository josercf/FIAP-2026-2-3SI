#!/usr/bin/env python3
"""Boss fight da ArenaLog. Rode com os cinco containers no ar.

Da sua máquina, localhost é a porta publicada. Entre containers o nome é o do Compose.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import uuid

ELENCO = "http://127.0.0.1:8081"
MOTOR = "http://127.0.0.1:8000"
PARTIDAS = "http://127.0.0.1:8080"
PLACAR = "http://127.0.0.1:8082"

PROIBIDAS = ("nome", "descricao", "atletaId", "latitude", "longitude")


class Falha(Exception):
    pass


def chamar(metodo, url, corpo=None):
    dados = None if corpo is None else json.dumps(corpo).encode("utf-8")
    requisicao = urllib.request.Request(
        url,
        data=dados,
        method=metodo,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=8) as resposta:
            texto = resposta.read().decode("utf-8")
            return resposta.status, json.loads(texto) if texto else {}
    except urllib.error.HTTPError as erro:
        texto = erro.read().decode("utf-8")
        try:
            corpo_erro = json.loads(texto) if texto else {}
        except json.JSONDecodeError:
            corpo_erro = {"erro": texto}
        return erro.code, corpo_erro


def exigir(condicao, mensagem):
    if not condicao:
        raise Falha(mensagem)


def chaves(valor, acumulado):
    if isinstance(valor, dict):
        for chave, item in valor.items():
            acumulado.add(chave)
            chaves(item, acumulado)
    elif isinstance(valor, list):
        for item in valor:
            chaves(item, acumulado)
    return acumulado


def main():
    for nome, base in (
        ("elenco", ELENCO),
        ("motor-ranking", MOTOR),
        ("partidas", PARTIDAS),
        ("placar", PLACAR),
    ):
        status, corpo = chamar("GET", f"{base}/health")
        exigir(status == 200 and corpo.get("status") == "ok", f"health {nome}: {status} {corpo}")
        print(f"HEALTH_{nome.upper().replace('-', '_')}: ok")

    status, atleta = chamar(
        "POST",
        f"{ELENCO}/api/v1/atletas",
        {"nome": "Lia Park", "campus": "Campus Norte", "canal": "ARENA"},
    )
    exigir(status == 201 and atleta.get("id"), f"elenco: {status} {atleta}")
    atleta_id = atleta["id"]
    print(f"ATLETA: {atleta_id}")

    def abrir(modalidade, campus, descricao):
        return chamar(
            "POST",
            f"{PARTIDAS}/api/v1/desafios",
            {
                "atletaId": atleta_id,
                "modalidade": modalidade,
                "descricao": descricao,
                "campus": campus,
            },
        )

    status, cartas = abrir(
        "CARTAS",
        "Centro",
        "Chave de cartas no intervalo, mesa 2 da arena.",
    )
    exigir(status == 201, f"cartas: {status} {cartas}")
    exigir(cartas.get("pontos") == 1 and cartas.get("faixa") == "BRONZE", cartas)
    exigir(cartas.get("janelaHoras") == 168 and cartas.get("serie") is False, cartas)
    exigir("nome" not in cartas, "desafio devolveu nome")
    print("CASO_CARTAS_CENTRO: 1 BRONZE 168 false")

    status, fps = abrir(
        "FPS",
        "Campus Norte",
        "Final de FPS no palco principal, serie ouro contra o norte.",
    )
    exigir(status == 201, f"fps: {status} {fps}")
    exigir(fps.get("pontos") == 5 and fps.get("faixa") == "LENDARIO", fps)
    exigir(fps.get("janelaHoras") == 8 and fps.get("serie") is False, fps)
    print("CASO_FPS_CAMPUS_NORTE: 5 LENDARIO 8 false")

    descricao_esporte = "Semifinal de esporte universitario no ginásio do rio."
    status, primeiro = abrir("ESPORTE", "Campus Rio", descricao_esporte)
    exigir(status == 201, f"esporte 1: {status} {primeiro}")
    status, segundo = abrir("ESPORTE", "Campus Rio", descricao_esporte + " Mesa B.")
    exigir(status == 201, f"esporte 2: {status} {segundo}")
    exigir(segundo.get("pontos") == 5 and segundo.get("faixa") == "LENDARIO", segundo)
    exigir(segundo.get("janelaHoras") == 8 and segundo.get("serie") is True, segundo)
    print("CASO_ESPORTE_CAMPUS_RIO_2: 5 LENDARIO 8 true")

    status, recusa = chamar(
        "PATCH",
        f"{PARTIDAS}/api/v1/desafios/{cartas['id']}/status",
        {"status": "ENCERRADO"},
    )
    exigir(status == 409, f"transicao: {status} {recusa}")
    status, ainda = chamar("GET", f"{PARTIDAS}/api/v1/desafios/{cartas['id']}")
    exigir(status == 200 and ainda.get("status") == "ABERTO", ainda)
    print("TRANSICAO_ILEGAL: 409")

    status, sumido = chamar(
        "POST",
        f"{PARTIDAS}/api/v1/desafios",
        {
            "atletaId": str(uuid.uuid4()),
            "modalidade": "MOBA",
            "descricao": "Desafio com atleta que o elenco não conhece.",
            "campus": "Centro",
        },
    )
    exigir(status == 404, f"atleta inexistente: {status} {sumido}")
    print("ATLETA_INEXISTENTE: 404")

    status, resumo = chamar(
        "GET", f"{PLACAR}/api/v1/resumo?campus=Campus%20Rio"
    )
    exigir(status == 200, f"resumo: {status} {resumo}")
    exigir(resumo.get("porFaixa", {}).get("LENDARIO") == 2, resumo)
    vistas = chaves(resumo, set())
    for proibida in PROIBIDAS:
        exigir(proibida not in vistas, f"resumo vazou {proibida}")
    exigir("id" not in vistas, "resumo vazou id")
    print("RESUMO_CAMPUS_RIO_LENDARIO: 2")
    print("RESUMO_SEM_DADO_PESSOAL: sim")
    print("BOSS: derrotado")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Falha, urllib.error.URLError, TimeoutError) as erro:
        print(f"BOSS: em pé ({erro})")
        sys.exit(1)
