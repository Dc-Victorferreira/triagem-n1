# triagem-n1

Classifica chamados de suporte por **categoria** e **prioridade** a partir do texto, e mede o cumprimento de **SLA** de primeiro atendimento e de solução. Sem dependências externas: só Python 3.10+.

Nasceu de uma automação real: no SAC eu perdia cerca de 3 horas por dia copiando pedidos do Outlook para uma planilha. Este é o mesmo tipo de problema resolvido de forma reproduzível e testável.

## O que faz

1. Lê um CSV de chamados (`exemplos/chamados.csv`).
2. Classifica cada chamado por palavras-chave definidas em `regras.json`.
3. Atribui prioridade conforme a categoria.
4. Calcula tempo de resposta e tempo de solução em minutos.
5. Marca estouro de SLA (resposta > 10 min, solução > 240 min).
6. Gera `saida/relatorio.csv` e imprime um resumo no terminal.

## Como rodar

```bash
python triagem.py exemplos/chamados.csv
```

Saída esperada:

```
Total de chamados: 16
Por categoria: {'Acesso/Contas': 5, 'Rede': 3, 'Software': 3, 'Hardware': 3, 'Impressora': 2}
Por prioridade: {'alta': 11, 'baixa': 3, 'media': 2}
SLA de resposta estourado: 6
SLA de solução estourado: 1
Tempo médio de primeira resposta: 16.6 min
Sem dados suficientes: 1 chamado(s)
Relatório gravado em saida/relatorio.csv
```

> No PowerShell, se os acentos aparecerem quebrados, rode `chcp 65001` antes ou defina `$env:PYTHONIOENCODING="utf-8"`. O CSV gerado já sai em UTF-8 com BOM e abre correto no Excel.

Arquivo gerado: `saida/relatorio.csv` (abre no Excel em português, com acentuação correta).

## Estrutura

```
triagem-n1/
├── triagem.py          # script principal
├── regras.json         # categorias, palavras-chave, prioridade e limites de SLA
├── exemplos/chamados.csv
└── saida/              # relatório gerado (ignorado pelo Git)
```

## Decisões de projeto

- **Regras fora do código.** `regras.json` permite mudar categorias e SLA sem tocar no Python — é o que um time de suporte precisa.
- **Classificação por contagem de palavras.** Se duas categorias casarem, ganha a que tiver mais palavras-chave. Simples e explicável; um modelo de NLP seria exagero para 16 chamados.
- **Dados ausentes não quebram o script.** Chamado sem data de encerramento aparece como "em aberto"; data inválida vira "sem dados" em vez de exceção.
- **Sem pandas.** O objetivo era rodar na máquina do trabalho, onde não se instala biblioteca.

## Limitações (honestas)

- Não entende sinônimo nem negação: "não consigo imprimir" casa com `imprimir`, mas "impressora ok" também casaria com `impressora`. Para produção, o certo é revisar a classificação manualmente ou usar um modelo.
- Não considera horário comercial nem feriado: o SLA é contado em minutos corridos.
- Os dados de `exemplos/` são fictícios, gerados para demonstração.

## O que eu aprenderia a seguir

- Testes com `pytest` para as funções `classificar` e `calcular_sla`.
- Leitura direta de exportação do GLPI em vez de CSV manual.
- Relatório em HTML com gráfico por categoria.

## Autor

Victor Arthur Ferreira — [LinkedIn](https://linkedin.com/in/victor-arthur-ferreira-064b282a0)
