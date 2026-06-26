# Handoff: organização da documentação (fonte única, índices, README de portfólio)

**Data:** 2026-06-26
**Status:** aguardando decisão (merge do PR `develop → main` é só do Weslley). Sessão de documentação concluída; backend intacto.

> **Há dois handoffs de 2026-06-26.** Este cobre a **sessão de organização da documentação**. Para o
> estado do **código** e o próximo passo de desenvolvimento (Fase 4 — dashboard), ver o irmão
> [handoff-2026-06-26-fase-3-fechada-e-stack-do-dashboard.md](handoff-2026-06-26-fase-3-fechada-e-stack-do-dashboard.md).
> A fonte de verdade do status é sempre o [roadmap.md](../roadmap.md).

## 1. Objetivo

"Organizar a casa": revisar e arrumar a documentação do projeto (sem tocar em código), eliminando
desatualizações e redundâncias, e deixando o repositório navegável para o próximo agente e
apresentável para recrutadores no GitHub. Nada de produção foi alterado — os 105 testes continuam
verdes.

## 2. Contexto essencial

- **O projeto:** software de aquisição de dados para hardware National Instruments (cDAQ-9184 + 2× 9205 + 1× 9235) em Python, substituindo o FlexLogger (pago). **Backend (Fases 0–3) completo**; próxima é a **Fase 4 (dashboard, PyQt6/pyqtgraph)**. Detalhe técnico no handoff irmão e no roadmap.
- **Stack:** Python 3.12, `pytest`, `uv` (Mac). `nidaqmx` é extra `[hardware]` (só Windows/Linux x86); `openpyxl` é extra `[excel]`. ~90% testável no Mac via adaptador `fake`.
- **Gatilho desta sessão:** uma revisão dos `.md` encontrou desatualização sistemática com uma causa única — informação volátil (fases, status, decisão de stack) estava **copiada** em vários arquivos, e duas mudanças recentes (renumeração de fases no roadmap + decisão do dashboard no ADR-013) não foram propagadas para todas as cópias.

## 3. O que já foi feito

Três commits na `develop` (nenhum toca código de produção):

**`bf48c43` — fonte única de informação volátil + ADR-014**
- **Unificada a numeração de fases.** O [roadmap.md](../roadmap.md) virou a **fonte única**; o `contexto-hardware.md §8` perdeu a lista de fases concorrente (esquema antigo de 4 fases) e virou resumo + link. Corrigidos para o esquema atual (**dashboard = Fase 4, validação física = Fase 5, empacotamento = Fase 6**): README, CLAUDE.md, `referencia-lynx.md`, `validacao-windows.md`, `tarefas-futuras.md`, `contexto-hardware.md`.
- **Propagada a decisão do dashboard** (ADR-013, PyQt6/pyqtgraph) para README, CLAUDE.md, contexto-hardware e tarefas-futuras (antes diziam "decisão adiada" e listavam Plotly/React).
- **Desduplicado o "Estudo de mercado"** — estava quase igual em `respostas-tio.md` e `referencia-flexlogger.md §5`; ficou só no §5 (dono), com ponteiro + resumo de uma linha no primeiro.
- **Criado o [ADR-014](../adr/014-fonte-unica-na-documentacao.md)**: política de **fonte única para informação volátil** (cada info tem um dono; os demais apontam, não copiam). Exceção deliberada: a armadilha do strain é repetida de propósito (segurança).

**`720db5d` — índices de navegação + regras de manutenção**
- Criado o **[índice de ADRs](../adr/README.md)** (`docs/adr/README.md`): tabela de uma linha por ADR (título, status, o que decide) + os "fios condutores" das substituições (008→010, etc.).
- Criada a **[nota dos handoffs](README.md)** (`docs/handoff/README.md`): ao retomar, ler **só o handoff de maior data**; o status real é o roadmap. Não cita o "mais recente" por nome de propósito (não virar ponto de desatualização).
- Adicionada ao CLAUDE.md a seção **"Manutenção da documentação (gatilho → ação)"** — tabela do que atualizar e quando.

**`9a74ef8` — README como vitrine + screenshot**
- **README reescrito como vitrine de portfólio** (em PT, revisado com a skill `/humanizer`): abre pelo problema real → diagrama Mermaid da arquitetura porta/adaptador → seção "Destaques de engenharia" → quickstart enxuto.
- Manual de uso detalhado movido para o novo **[docs/uso.md](../uso.md)**.
- Adicionada **screenshot da suíte de testes** em `docs/assets/testes.png` (105 testes verdes no Mac), logo após o pitch. `docs/assets/` é versionada — **distinta de `docs/img/`, que é ignorada** (prints de cliente).

**Memória salva:** `priorizar-contexto-sobre-tokens` (o Weslley teme estourar a janela de contexto, não o custo; ler seletivo, não "consumir docs inteira").

## 4. Estado atual

- **Working tree limpo** após os 3 commits (este handoff será o 4º commit).
- **105 testes verdes** (`uv run pytest`) — esta sessão não tocou código.
- **PR `develop → main` ainda não aberto.** O diff contém exatamente os 3 commits de docs acima (13 arquivos; todo o backend anterior já está na `main` via PR #4).
- Documentação coerente: numeração de fases unificada, sem stack obsoleta (zero menções a Plotly/React), índices criados, README de portfólio.

## 5. Bloqueios e dependências

- **Merge na `main` é só do Weslley** — ele fará após revisar o PR.
- **TXT-AqAnalysis provisório** e **número físico do strain** seguem pendentes (Fase 5, hardware do tio) — não bloqueiam nada desta sessão. Ver [tarefas-futuras.md](../tarefas-futuras.md).
- Nenhum bloqueio técnico nesta frente de documentação.

## 6. Próximos passos

Nesta frente (publicação):
1. Commitar este handoff.
2. `git push origin develop`.
3. Abrir o PR `develop → main` com `gh pr create` (descrição caprichada).
4. Weslley revisa e faz o **merge**.

No projeto (próxima sessão de desenvolvimento, em outro chat):
5. **Fase 4 — dashboard.** Começar pelo **design/UX** (não sair codando tela), espelhando o AqDados (ver `referencia-lynx.md`): tabela de canais, aferição (pontos + regressão + correlação + tara), controle de ensaio e **visualização em tempo real** (sinal×tempo, XY carga×deformação, FFT). Implementar com PyQt6/pyqtgraph consumindo a porta `FonteDeAquisicao` (fake no Mac). Nova camada `src/ensaios_ni/apresentacao/`. Detalhe no handoff irmão e no roadmap.

## 7. Artefatos relevantes

- **Política e navegação:** [docs/adr/014-fonte-unica-na-documentacao.md](../adr/014-fonte-unica-na-documentacao.md), [docs/adr/README.md](../adr/README.md), [docs/handoff/README.md](README.md), seção "Manutenção da documentação" no [CLAUDE.md](../../CLAUDE.md).
- **Vitrine:** [README.md](../../README.md), [docs/uso.md](../uso.md), `docs/assets/testes.png`.
- **Fonte de status:** [docs/roadmap.md](../roadmap.md).
- **Comandos úteis:**
  - `uv run pytest` → 105 passed.
  - Demo + screenshot: `clear && uv run pytest` (foi a base da screenshot do README).
  - PR: `git push origin develop` depois `gh pr create --base main --head develop`.

## 8. Como iniciar a próxima sessão

- **Se for continuar a publicação (esta frente):** confirmar com o Weslley se o **PR foi mergeado**; se sim, sincronizar a `develop` com a `main`.
- **Se for desenvolvimento (Fase 4):** ler o handoff irmão [handoff-2026-06-26-fase-3-fechada-e-stack-do-dashboard.md](handoff-2026-06-26-fase-3-fechada-e-stack-do-dashboard.md) + o [roadmap.md](../roadmap.md) + a [referencia-lynx.md](../referencia-lynx.md); rodar `uv run pytest` (105 passed) para confirmar a base; **não codar tela ainda** — rodar o discovery de UX primeiro (skill `/planejar-ux` ou `/criar-ui`).
- **Regras de sempre:** `import nidaqmx` só no `daqmx.py` (lazy); strain nunca usa defaults da API; português em tudo; commits separados por camada; nada de commit/push/merge autônomo.
