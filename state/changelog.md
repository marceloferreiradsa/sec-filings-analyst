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

## 2026-10-20 — Adoção do método

**Mudança:** a estrutura do `ai-project-framework` (versão `2f39f84`) foi instalada pelo
caso B — `CLAUDE.md`, `METODO.md`, `COMO-ADOTAR.md`, `tools/`, `.template/`, `refs/` e
`.gitattributes`. O `Makefile` do método **não** foi copiado: virou `metodo.mk`, incluído
na última linha do `Makefile` do projeto, com `check`/`index`/`help`/`test`/`clean`
renomeados para `docs-check`/`docs-index`/`metodo-*` e as 36 citações reescritas nas
cópias do método (ADR-12). `.gitignore` completado com as entradas do método e com
`*.tar.gz` (imagem Docker de 237 MB solta na raiz). `docs/` — que nunca tinha sido
commitada — entra agora: decisões viraram ADR-01..11 e features FEAT-01..09, todas com
Status. Índice: 0 → 21 registros.

**Por quê:** RAG muda constantemente de funcionalidade e recebe aprimoramentos o tempo
todo; é uma arquitetura que exige acompanhamento contínuo das decisões, para que caminhos
já descartados não sejam retomados sem fundamentação suficiente.

**Documentos tocados:** todos os do método · `Makefile` (include) · `metodo.mk` (novo) ·
`.gitignore` · `docs/ARCHITECTURAL_DECISIONS.md` (cabeçalhos, Status, ADR-12) ·
`docs/NEXT_FEATURES.md` (cabeçalhos, Status) · `CLAUDE.md` (O que é este projeto;
Convenções; nota de adoção removida) · `state/aberto.md`

**Registros:** ADR-12 criado · AD-01, AD-02, AD-03 resolvidas · AB-01 e AB-02 abertas

**Pendente:** AB-01 (aceitar ou não o `ROADMAP_PRIORITIES`) · AB-02 (migrar alvos quando o
framework padronizar o prefixo) · AD-04 (primeiro handoff real) · AD-05 · AD-06.

---
