# ADR 014 — Fonte única para informação volátil na documentação

## Status

Aceito (26/06/2026)

## Contexto

A documentação do projeto cresceu para ~30 arquivos `.md` (README, CLAUDE.md, CONTEXT.md, 13 ADRs,
referências, handoffs, runbooks). Numa revisão de 26/06/2026 encontramos **desatualização
sistemática** com uma causa comum: informação que **muda a cada fase** estava **copiada** em vários
arquivos, e duas mudanças recentes não foram propagadas para todas as cópias.

- A **numeração das fases** divergia entre três documentos: o [roadmap.md](../roadmap.md) (esquema
  novo, 0–6, dashboard = Fase 4) contra o [contexto-hardware.md §8](../contexto-hardware.md) (esquema
  antigo, 0–4, dashboard = Fase 3) e o [CLAUDE.md](../../CLAUDE.md). Quem cruzasse os dois não sabia
  se o dashboard era Fase 3 ou 4.
- A **decisão de stack do dashboard** ([ADR-013](013-stack-do-dashboard.md): PyQt6/pyqtgraph) não
  chegou ao README, ao CLAUDE.md, ao `contexto-hardware.md` nem ao `tarefas-futuras.md` — que ainda
  diziam "decisão adiada" e listavam Plotly/React.
- O **"estudo de mercado" (23/06)** estava duplicado quase igual em
  [respostas-tio.md](../respostas-tio.md) e [referencia-flexlogger.md §5](../referencia-flexlogger.md).

Agravante específico deste projeto: o `CLAUDE.md` é carregado pelo agente (Claude Code) **a cada
turno**. Se ele guarda estado volátil copiado e desatualizado, o agente recebe informação errada
como se fosse regra.

## Decisão

**Cada informação volátil tem um dono único; os demais documentos apontam (link), não copiam.**

Donos definidos:

| Informação | Dono único | Os demais |
| ---------- | ---------- | --------- |
| Plano em fases e **status** ("onde estamos") | [roadmap.md](../roadmap.md) | linkam |
| Decisões de arquitetura e o porquê | [docs/adr/](.) | linkam o ADR |
| Glossário do domínio | [CONTEXT.md](../../CONTEXT.md) | linkam |
| Inventário de hardware + API pinada do `nidaqmx` | [contexto-hardware.md](../contexto-hardware.md) | linkam |
| Protocolo de dúvida + filosofia de produto | [onde-pesquisar.md](../onde-pesquisar.md) | linkam |
| Pesquisa técnica do driver (FlexLogger/DAQmx) | [referencia-flexlogger.md](../referencia-flexlogger.md) | linkam |
| Produto / UX / vocabulário (Lynx) | [referencia-lynx.md](../referencia-lynx.md) | linkam |

Regras operacionais:

- **O `CLAUDE.md` guarda só regra estável + ponteiros.** Nunca status de fase nem decisão volátil
  copiada — referencia o dono (`ver ADR-013`, `ver roadmap.md`). É o documento mais lido pelo
  agente; tem que ser confiável.
- **Documento secundário não recopia o conteúdo do dono** — resume em uma linha (quando a leitura
  local exigir) e linka. Ex.: `respostas-tio.md` cita o estudo de mercado em uma frase e aponta para
  `referencia-flexlogger.md §5`.
- **`contexto-hardware.md §8` não mantém lista de fases própria** — resume o estado e linka o roadmap.
- **Handoffs e o CHANGELOG são append-only e datados** — registram o momento, não são fonte de
  verdade do estado atual (o roadmap é). Podem citar fases; não precisam ser reescritos quando o
  plano muda.

Exceção deliberada: **redundância de segurança é permitida.** A armadilha do strain (quarter-bridge
120 Ω / 2,0 V vs os defaults perigosos da API) aparece de propósito em vários lugares (CLAUDE.md,
contexto-hardware §4, [ADR-009](009-leitura-de-strain-9235.md), CONTEXT.md, validacao-windows,
comentários no código). É o maior risco do projeto — a repetição é proteção, não drift.

## Consequências

**Melhora:**

- Um único lugar para atualizar quando a fase/decisão muda → some o drift entre cópias.
- O `CLAUDE.md` deixa de alimentar o agente com estado obsoleto.
- Avançar de fase ou adicionar um ADR não exige caçar todas as cópias.

**Piora / custo:**

- Exige disciplina de **linkar em vez de colar** — o reflexo natural é copiar.
- O leitor às vezes precisa seguir um link para ver o detalhe (ex.: o estudo de mercado completo).
- Um resumo de uma linha no documento secundário ainda pode envelhecer; mantê-lo curto e factual
  minimiza isso.

**Aplicação:** a revisão de 26/06/2026 aplicou esta política retroativamente — unificou a numeração
de fases, propagou o ADR-013 e desduplicou o estudo de mercado. Ver `CHANGELOG.md`.
