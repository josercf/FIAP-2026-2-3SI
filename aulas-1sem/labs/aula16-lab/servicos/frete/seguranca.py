"""Validação de JWT por JWKS, sem nenhuma dependência externa.

Este arquivo aparece **repetido** em cada serviço Python da plataforma
(`frete`, `ai-gateway`, `rag`). Não é descuido: microsserviço não compartilha
biblioteca interna por padrão, e um pacote comum obrigaria os três a subirem
juntos a cada correção. A duplicação é a escolha, e está declarada aqui.

Por que RS256 escrito à mão em vez de PyJWT
-------------------------------------------
Verificar uma assinatura RS256 é aritmética modular sobre um inteiro grande,
e o Python já traz `pow(base, expoente, modulo)` e `hashlib`. Escrever isso
com a biblioteca padrão custa trinta linhas, não acrescenta um pacote que
precisa de compilador na imagem Alpine, e deixa visível o que o backend está
de fato conferindo: que `assinatura ** e mod n` reconstrói o hash do
cabeçalho e do payload.

O contrato é o da ADR-009:

    LOGITECH_AUTH_ATIVA       false por padrão; a Aula 14 liga
    LOGITECH_OIDC_ISSUER      o `iss` que o token precisa trazer
    LOGITECH_OIDC_JWKS_URL    de onde as chaves públicas são lidas

O papel viaja em `realm_access.roles` e é **daí** que todo serviço lê. Metade
dos exemplos da internet lê de `resource_access.<client>.roles`, e um serviço
lendo de um lugar e outro do outro produz autorização que funciona no Java e
falha no Node, com o mesmo token.

Não é tarefa. Este arquivo vem pronto.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.request

# Prefixo DigestInfo do PKCS#1 v1.5 para SHA-256 (RFC 8017, seção 9.2).
# É a sequência ASN.1 que identifica o algoritmo de hash dentro do bloco
# assinado. Sem conferi-la, um atacante poderia trocar o algoritmo.
_DIGEST_INFO_SHA256 = bytes.fromhex("3031300d060960864801650304020105000420")

_CACHE_JWKS: dict = {"em": 0.0, "chaves": {}}
_VALIDADE_DO_CACHE_S = 300


class ErroDeToken(Exception):
    """Token ausente, malformado, expirado ou com assinatura inválida."""


class ErroDePapel(Exception):
    """Token válido, mas sem o papel que a rota exige."""


def ativa() -> bool:
    """A autenticação só entra em vigor com LOGITECH_AUTH_ATIVA ligada.

    Padrão `false`, como a ADR-009 fixou: os laboratórios das Aulas 05 a 12
    foram escritos sem autenticação e continuam passando com ela desligada.
    Isto não é porta dos fundos escondida: está no README, no slide e o
    verificador da Aula 16 **exige** a variável ligada.
    """
    return os.environ.get("LOGITECH_AUTH_ATIVA", "false").strip().lower() in (
        "1", "true", "sim", "on",
    )


def _b64url(dado: str) -> bytes:
    return base64.urlsafe_b64decode(dado + "=" * (-len(dado) % 4))


def _inteiro(dado: str) -> int:
    return int.from_bytes(_b64url(dado), "big")


def _jwks() -> dict:
    """Baixa e guarda as chaves públicas do provedor de identidade.

    O cache de cinco minutos é o motivo de o backend **não** consultar o
    Keycloak a cada requisição: a chave pública muda raramente, o token traz
    o `kid` que diz qual usar, e a validação é local.
    """
    agora = time.time()
    if _CACHE_JWKS["chaves"] and agora - _CACHE_JWKS["em"] < _VALIDADE_DO_CACHE_S:
        return _CACHE_JWKS["chaves"]

    url = os.environ.get("LOGITECH_OIDC_JWKS_URL", "")
    if not url:
        raise ErroDeToken("LOGITECH_OIDC_JWKS_URL não configurada")

    with urllib.request.urlopen(url, timeout=5) as resposta:
        documento = json.loads(resposta.read().decode("utf-8"))

    chaves = {k["kid"]: k for k in documento.get("keys", []) if k.get("kty") == "RSA"}
    if not chaves:
        raise ErroDeToken("o JWKS não trouxe nenhuma chave RSA")
    _CACHE_JWKS.update(em=agora, chaves=chaves)
    return chaves


def _confere_assinatura(cabecalho: dict, assinado: bytes, assinatura: bytes) -> None:
    if cabecalho.get("alg") != "RS256":
        raise ErroDeToken("algoritmo %r recusado: só RS256" % cabecalho.get("alg"))

    chave = _jwks().get(cabecalho.get("kid"))
    if chave is None:
        _CACHE_JWKS["chaves"] = {}          # kid novo: força recarga do JWKS
        chave = _jwks().get(cabecalho.get("kid"))
    if chave is None:
        raise ErroDeToken("kid %r não está no JWKS" % cabecalho.get("kid"))

    n = _inteiro(chave["n"])
    e = _inteiro(chave["e"])
    tamanho = (n.bit_length() + 7) // 8

    if len(assinatura) != tamanho:
        raise ErroDeToken("assinatura com tamanho inesperado")

    # A verificação inteira cabe nesta linha: eleva a assinatura ao expoente
    # público. Só quem tem a chave privada consegue produzir um número que
    # sobrevive a essa conta com o padding correto do outro lado.
    recuperado = pow(int.from_bytes(assinatura, "big"), e, n).to_bytes(tamanho, "big")

    esperado = (
        b"\x00\x01"
        + b"\xff" * (tamanho - len(_DIGEST_INFO_SHA256) - 35)
        + b"\x00"
        + _DIGEST_INFO_SHA256
        + hashlib.sha256(assinado).digest()
    )
    if recuperado != esperado:
        raise ErroDeToken("assinatura inválida")


def validar(cabecalho_authorization: str | None) -> dict:
    """Valida `Authorization: Bearer <token>` e devolve as claims.

    Levanta `ErroDeToken`, que o chamador traduz em **401**.
    """
    if not cabecalho_authorization or not cabecalho_authorization.lower().startswith("bearer "):
        raise ErroDeToken("cabeçalho Authorization ausente ou sem o esquema Bearer")

    token = cabecalho_authorization.split(None, 1)[1].strip()
    partes = token.split(".")
    if len(partes) != 3:
        raise ErroDeToken("o token não tem as três partes de um JWT")

    try:
        cabecalho = json.loads(_b64url(partes[0]))
        claims = json.loads(_b64url(partes[1]))
        assinatura = _b64url(partes[2])
    except Exception as erro:                       # noqa: BLE001
        raise ErroDeToken("token malformado: %s" % erro) from erro

    _confere_assinatura(cabecalho, ("%s.%s" % (partes[0], partes[1])).encode("ascii"), assinatura)

    agora = time.time()
    if claims.get("exp", 0) < agora:
        raise ErroDeToken("token expirado")
    if claims.get("nbf", 0) > agora + 60:
        raise ErroDeToken("token ainda não é válido")

    issuer = os.environ.get("LOGITECH_OIDC_ISSUER", "")
    if issuer and claims.get("iss") != issuer:
        # Este é o erro que mais custou tempo na construção do acervo. O
        # `iss` que o Keycloak grava é o endereço pelo qual o NAVEGADOR o
        # alcançou (`localhost:8090`); o endereço pelo qual o backend busca
        # o JWKS é o da rede interna (`keycloak:8090`). São dois valores
        # diferentes e as duas variáveis existem por causa disso.
        raise ErroDeToken(
            "issuer divergente: o token traz %r e este serviço espera %r"
            % (claims.get("iss"), issuer)
        )
    return claims


def papeis(claims: dict) -> set:
    """Lê os papéis de `realm_access.roles`, e de nenhum outro lugar."""
    return {str(p).upper() for p in (claims.get("realm_access") or {}).get("roles", [])}


def exigir(cabecalho_authorization: str | None, *aceitos: str) -> dict:
    """Valida o token e confere o papel.

    Sem token: `ErroDeToken`, que vira **401**.
    Token bom e papel errado: `ErroDePapel`, que vira **403**.
    A diferença entre os dois é conteúdo de aula e critério do verificador.
    """
    claims = validar(cabecalho_authorization)
    if aceitos:
        tenho = papeis(claims)
        if not tenho & {p.upper() for p in aceitos}:
            raise ErroDePapel(
                "este token tem %s e a rota exige um de %s"
                % (sorted(tenho) or "nenhum papel", sorted(aceitos))
            )
    return claims


def origens_cors() -> list:
    """Origens permitidas, do contrato da ADR-008."""
    bruto = os.environ.get(
        "LOGITECH_CORS_ORIGINS", "http://localhost:5173,http://localhost:4200"
    )
    return [o.strip() for o in bruto.split(",") if o.strip()]
