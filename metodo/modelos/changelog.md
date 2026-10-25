# Changelog

> **Append-only.** Uma entrada por alteração, escrita **no momento em que acontece**.
> Nunca reescrever nem reorganizar. Entradas mais recentes no topo.
>
> Este arquivo responde "por que isto está assim?" meses depois. O git mostra o
> que mudou; aqui fica o motivo.

**Formato:**
```
## AAAA-MM-DD — título curto

**Mudança:** o que foi feito e por que.
**Documentos tocados:** arquivo (seção) · arquivo (seção)
**Registros:** ADR-NN criado · pendência NN resolvida
**Pendente:** o que ficou (também vai para aberto.md) — ou "nada"
```

---

## AAAA-MM-DD — Adoção do método

**Mudança:** a estrutura do `ai-project-framework` foi instalada neste projeto —
`CLAUDE.md`, a pasta `metodo/` (scripts, modelos e racional) e `refs/`. Os comandos do
método rodam por `python -m metodo`; o `Makefile` é só do projeto. O estado nasceu
com as pendências da adoção em `aberto.md`, prefixadas `AD-`.

**Versão do template:** {VERSAO}

**Por quê:** *(uma frase sua sobre por que este projeto precisa de continuidade
documentada. Pode ficar para depois — mas se ficar vazia, ninguém saberá em seis meses
se a adoção foi decisão ou inércia.)*

**Documentos tocados:** todos os do método

**Registros:** AD-01 a AD-06 abertas

**Pendente:** as `AD-` que ainda não foram riscadas.

---
