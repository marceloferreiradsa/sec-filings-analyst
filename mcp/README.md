# Servidores MCP próprios

Coloque aqui servidores MCP escritos para este projeto.

**Quando vale escrever um:** quando o agente precisa repetidamente de uma operação
que não é arquivo nem shell — consultar uma API interna, ler um sistema proprietário,
executar uma query num banco com credencial gerenciada.

**Quando não vale:** se um comando de shell ou um script resolve. MCP adiciona uma
camada de protocolo; só compensa quando a operação é recorrente e estruturada.

## Estrutura mínima (Python)

Um servidor MCP expõe *tools* (ações), *resources* (leitura) e *prompts*. O SDK
oficial cuida do protocolo; você escreve as funções.

```
pip install mcp
```

Registre em `.mcp.json` na raiz do projeto (veja `.mcp.json.example`) e confirme
com `python -m metodo mcp-list`.

## Regras deste template

- **Credencial nunca no arquivo versionado.** Use `${VARIAVEL}` e defina no ambiente.
- Um servidor por domínio, não um servidor que faz tudo.
- Documente cada tool com o que ela faz **e o que ela não faz** — o agente decide
  por essa descrição.
