#!/usr/bin/env python3
"""Cria a proxima divida tecnica em docs/dividas_tecnicas.md.

Le o maior numero existente e incrementa. Numeracao nunca e reaproveitada: uma
divida paga muda de status, nunca some — saber que algo foi aceito e por quanto
tempo vale tanto quanto saber que foi resolvido.

Por que a divida tem documento proprio, e nao vive em state/aberto.md:

    aberto.md e lido POR INTEIRO no inicio de toda sessao, e seu contrato e
    reconstruir contexto em ~100 linhas. Divida com impacto dimensionado gasta
    umas 20 linhas cada; dezessete delas somam mais de 500. Os dois nao cabem
    no mesmo arquivo sem destruir a economia de contexto.

    Alem do tamanho, sao coisas diferentes. aberto.md guarda ACAO pendente, e a
    pendencia e riscada quando morre. Divida e PROPRIEDADE conhecida do sistema,
    com custo medido: ela muda de status e fica, porque continua explicando por
    que o sistema e como e. E divida com status Aceita nunca vira acao nenhuma.

    E docs/ entra no indice; state/ nao. Divida em aberto.md seria invisivel ao
    passo 1 do protocolo — justamente quando alguem esta prestes a mexer no
    assunto que ela cobre.

A fronteira, quando as duas se tocam: a divida e o registro canonico (o que e,
quanto custa, quando resolver). A acao de paga-la, enquanto estiver ativa, e uma
pendencia em aberto.md que APONTA para o DT. Sem essa regra escrita, com poucas
dividas e todas com acao ativa, os dois arquivos parecem duplicados.
"""
import re
import sys
from datetime import date
from pathlib import Path

# Windows: sem isto, o stdout sai em cp1252 e corrompe os acentos das mensagens.
sys.stdout.reconfigure(encoding="utf-8")

# Nome de arquivo especifico do idioma: traduzir numa versao em outro idioma.
DOC = Path("docs/dividas_tecnicas.md")

CABECALHO = (
    "# Dívidas Técnicas\n\n"
    "> Registro consolidado das dívidas conhecidas do projeto: o que é sub-ótimo\n"
    "> hoje, por que ficou assim, quanto custa manter e quando vale resolver.\n>\n"
    "> **Status:** Aberta · Em pagamento · Paga · Aceita\n"
    "> **Prioridade:** Alta · Média · Baixa\n>\n"
    "> Os dois são rótulos curtos, em texto puro: sobem para `docs/_index.md` e é\n"
    "> por eles que o protocolo decide se pode agir. Glifo não atravessa conversão\n"
    "> e não se procura por ele. Comentário vai depois de um ponto; o índice\n"
    "> descarta dali para a frente.\n>\n"
    "> **`Aceita` não é o mesmo que `Paga`.** Aceita é a decisão de conviver com a\n"
    "> dívida; ela fica registrada para sempre e nunca vira tarefa.\n>\n"
    "> **Não mantenha um índice por prioridade aqui.** Ele apodrece em silêncio —\n"
    "> a mesma entrada acaba listada em dois grupos. `make docs-index` já publica ID,\n"
    "> título, status e prioridade em `docs/_index.md`.\n>\n"
    "> **Divida ≠ pendência.** Aqui fica o registro canônico. A ação de pagá-la,\n"
    "> enquanto ativa, é uma pendência em `state/aberto.md` que aponta para o DT.\n\n"
    "---\n"
)

MODELO = """
<a id="dt-{n:02d}"></a>

## DT-{n:02d} — {title}

**Status:** Aberta
**Prioridade:** Média

**Descrição:** o que é sub-ótimo hoje, em uma frase objetiva.

**Por que ficou assim:** o contexto que levou a aceitar — prazo, informação que
ainda não existia, desbloqueio de outra frente. Sem isto, meses depois a dívida
parece descuido.

**Custo de manter:** o impacto dimensionado — e também **o que ele não afeta**.
Esta seção é a que distingue dívida de anotação: sem ela ninguém sabe o preço de
não pagar, e a priorização vira palpite.

**Esforço para resolver:** o que concretamente fecha a dívida.

**Quando resolver:** o gatilho ou a barreira de entrega. É o que torna a dívida
acionável sem que ela precise virar tarefa.

**Relacionada:** ADR-NN, se nasceu de uma decisão. Ou `—`.

*Registrada em {today}.*

---
"""


def main():
    if not DOC.exists():
        DOC.parent.mkdir(parents=True, exist_ok=True)
        DOC.write_text(CABECALHO, encoding="utf-8", newline="\n")
    text = DOC.read_text(encoding="utf-8")
    numbers = [int(m) for m in re.findall(r"^## DT-(\d+)", text, re.M)]
    n = max(numbers) + 1 if numbers else 1
    title = input(f"Título da DT-{n:02d}: ").strip() or "TODO"
    DOC.write_text(
        text.rstrip() + "\n" + MODELO.format(n=n, title=title, today=date.today().isoformat()),
        encoding="utf-8", newline="\n",
    )
    print(f"  DT-{n:02d} criada em {DOC}")
    print("  Se houver ação ativa para pagá-la, abra a pendência em state/aberto.md")
    print("  Não esqueça: make docs-index")


if __name__ == "__main__":
    main()
