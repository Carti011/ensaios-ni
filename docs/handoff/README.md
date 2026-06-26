# Handoffs — ensaios-ni

Registros de fim de sessão, **append-only e datados** (`handoff-AAAA-MM-DD-tema.md`). Cada um resume
o estado no momento em que foi escrito. Gerados pela skill `/handoff`.

## Ao retomar o projeto num chat novo

1. **Leia só o handoff de data mais recente** — o arquivo com o maior `AAAA-MM-DD` no nome
   (`ls docs/handoff/` e pegue o último). Ele resume o estado atual; os anteriores são **histórico**,
   não os leia para saber "onde estamos".
2. A **fonte de verdade do status** é o [roadmap.md](../roadmap.md), não os handoffs
   ([ADR-014](../adr/014-fonte-unica-na-documentacao.md)). Se um handoff antigo conflitar com o
   roadmap, vale o roadmap.
3. O **índice de decisões** é [docs/adr/README.md](../adr/README.md); as regras invariáveis estão no
   [CLAUDE.md](../../CLAUDE.md) (carregado automaticamente). O **roteador de dúvidas** é
   [onde-pesquisar.md](../onde-pesquisar.md).

> **Por que não ler todos os handoffs:** um agente que lê os 6 gasta janela de contexto com estado
> **velho** e arrisca agir sobre informação superada — o oposto do que protege contra alucinação. O
> handoff mais recente + o roadmap bastam para orientar; o resto se lê **sob demanda**, seguindo os
> ponteiros acima. Não duplicamos aqui o nome do "mais recente" justamente para este README não virar
> mais um ponto de desatualização (ADR-014) — ordene por data e pegue o último.
