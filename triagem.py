#!/usr/bin/env python3
"""Classifica chamados de suporte por categoria e prioridade e mede SLA.

Uso:
    python triagem.py exemplos/chamados.csv
    python triagem.py chamados.csv --saida saida/relatorio.csv --config regras.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

FORMATO_DATA = "%Y-%m-%d %H:%M"
CAMPOS_SAIDA = [
    "id", "data_abertura", "canal", "solicitante", "assunto",
    "categoria", "prioridade", "status", "tempo_resposta_min",
    "tempo_solucao_min", "sla_resposta", "sla_solucao",
]


def carregar_regras(caminho: Path) -> dict:
    with open(caminho, encoding="utf-8") as arquivo:
        regras = json.load(arquivo)
    if "categorias" not in regras or not regras["categorias"]:
        raise ValueError(f"{caminho}: falta a chave 'categorias' ou ela está vazia")
    return regras


def classificar(assunto: str, descricao: str, regras: dict) -> tuple[str, str]:
    """Devolve (categoria, prioridade). Ganha a categoria com mais palavras-chave."""
    texto = f"{assunto or ''} {descricao or ''}".lower()
    melhor_categoria = "Indefinido"
    melhor_prioridade = "baixa"
    melhor_pontuacao = 0

    for nome, regra in regras["categorias"].items():
        palavras = regra.get("palavras", [])
        pontos = sum(1 for palavra in palavras if palavra.lower() in texto)
        if pontos > melhor_pontuacao:
            melhor_pontuacao = pontos
            melhor_categoria = nome
            melhor_prioridade = regra.get("prioridade", "media")

    return melhor_categoria, melhor_prioridade


def ler_data(valor: str | None) -> datetime | None:
    valor = (valor or "").strip()
    if not valor:
        return None
    try:
        return datetime.strptime(valor, FORMATO_DATA)
    except ValueError:
        return None


def diferenca_minutos(inicio: datetime | None, fim: datetime | None) -> int | None:
    if inicio is None or fim is None:
        return None
    return round((fim - inicio).total_seconds() / 60)


def avaliar_sla(minutos: int | None, limite: int) -> str:
    if minutos is None:
        return "sem dados"
    return "ok" if minutos <= limite else "estourado"


def processar(linhas: list[dict], regras: dict) -> list[dict]:
    limite_resposta = regras.get("sla", {}).get("primeiro_atendimento_min", 10)
    limite_solucao = regras.get("sla", {}).get("solucao_min", 240)

    resultado = []
    for linha in linhas:
        categoria, prioridade = classificar(
            linha.get("assunto", ""), linha.get("descricao", ""), regras
        )
        abertura = ler_data(linha.get("data_abertura"))
        primeiro = ler_data(linha.get("data_primeiro_atendimento"))
        encerramento = ler_data(linha.get("data_encerramento"))

        tempo_resposta = diferenca_minutos(abertura, primeiro)
        tempo_solucao = diferenca_minutos(abertura, encerramento)

        resultado.append({
            "id": linha.get("id", ""),
            "data_abertura": linha.get("data_abertura", ""),
            "canal": linha.get("canal", ""),
            "solicitante": linha.get("solicitante", ""),
            "assunto": linha.get("assunto", ""),
            "categoria": categoria,
            "prioridade": prioridade,
            "status": linha.get("status", ""),
            "tempo_resposta_min": "" if tempo_resposta is None else tempo_resposta,
            "tempo_solucao_min": "" if tempo_solucao is None else tempo_solucao,
            "sla_resposta": avaliar_sla(tempo_resposta, limite_resposta),
            "sla_solucao": avaliar_sla(tempo_solucao, limite_solucao),
        })
    return resultado


def gravar_csv(linhas: list[dict], caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig para o Excel em português reconhecer a acentuação
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_SAIDA)
        escritor.writeheader()
        escritor.writerows(linhas)


def resumir(linhas: list[dict]) -> None:
    print(f"Total de chamados: {len(linhas)}")
    por_categoria = Counter(l["categoria"] for l in linhas)
    por_prioridade = Counter(l["prioridade"] for l in linhas)
    print(f"Por categoria: {dict(por_categoria.most_common())}")
    print(f"Por prioridade: {dict(por_prioridade.most_common())}")

    resposta = [l["tempo_resposta_min"] for l in linhas if l["tempo_resposta_min"] != ""]
    print(f"SLA de resposta estourado: {sum(l['sla_resposta'] == 'estourado' for l in linhas)}")
    print(f"SLA de solução estourado: {sum(l['sla_solucao'] == 'estourado' for l in linhas)}")
    if resposta:
        print(f"Tempo médio de primeira resposta: {sum(resposta) / len(resposta):.1f} min")
    pendentes = [l for l in linhas if l["sla_resposta"] == "sem dados"]
    if pendentes:
        print(f"Sem dados suficientes: {len(pendentes)} chamado(s)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classifica chamados e mede SLA.")
    parser.add_argument("entrada", help="CSV de chamados")
    parser.add_argument("--saida", default="saida/relatorio.csv", help="CSV de saída")
    parser.add_argument("--config", default="regras.json", help="JSON de regras")
    args = parser.parse_args(argv)

    try:
        regras = carregar_regras(Path(args.config))
        with open(args.entrada, encoding="utf-8") as arquivo:
            linhas = list(csv.DictReader(arquivo))
        if not linhas:
            print("CSV vazio.", file=sys.stderr)
            return 1
        resultado = processar(linhas, regras)
        gravar_csv(resultado, Path(args.saida))
    except FileNotFoundError as erro:
        print(f"Arquivo não encontrado: {erro.filename}", file=sys.stderr)
        return 1
    except (ValueError, KeyError) as erro:
        print(f"Erro de configuração: {erro}", file=sys.stderr)
        return 1

    resumir(resultado)
    print(f"Relatório gravado em {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
