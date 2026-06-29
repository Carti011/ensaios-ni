# Handoff: avaliação crítica, saúde da documentação e README de portfólio

**Data:** 2026-06-28
**Status:** sessão **só de documentação** (nenhum código de produção tocado; **178 testes** seguem
verdes). Commitada na `develop` e **PR `develop → main` aberta** nesta sessão — **merge é do Weslley**.

> **Há dois handoffs de 2026-06-28.** Este é o **mais recente** e cobre a sessão de
> **avaliação/documentação/portfólio**. O outro
> ([Fase 4 fechada — metadata, exportar e tara](handoff-2026-06-28-fase-4-fechada-metadata-exportar-tara.md))
> cobre o fechamento do dashboard (código). A fonte de verdade do status é o [roadmap.md](../roadmap.md).

## 1. Objetivo

A Fase 4 (dashboard) fechou; o Weslley pediu uma **avaliação crítica honesta** do projeto (ele não
consegue se autoavaliar) e, a partir dela, **arrumar a casa**: registrar as urgências, reorganizar a
documentação operacional e transformar o README numa **peça de portfólio** pronta para recrutadores.
Nenhuma linha de código de produção foi alterada.

## 2. Contexto essencial

- **Backend + dashboard completos** (Fases 0–4), 178 testes no Mac com o `fake`. O que separa o tio
  de usar **não é software no Mac** — é hardware real, `.exe` e o elo com a análise dele. Essa é a
  tese desta sessão, formalizada no **[ADR-019](../adr/019-foco-em-validacao-fisica-e-adocao.md)**.
- **Filosofia inalterada:** usuário é o **tio** (OFM); o critério de sucesso é ele **largar o
  FlexLogger**. A avaliação foi feita testando de verdade (rodei a suíte, gerei um ensaio pela CLI,
  abri o dashboard) e pesquisando como o **FlexLogger** funciona (fontes registradas na conversa).
- **Política de documentação (ADR-014):** cada informação volátil tem um dono; os demais apontam.
  Esta sessão aplicou isso ao reorganizar os guias.

## 3. O que já foi feito (cronológico)

1. **Avaliação crítica** → `docs/avaliacao-critica.md` (documento de trabalho **temporário**): o que
   está bom e os gaps que separam o projeto da adoção, **priorizados por gravidade** (🔴 bloqueia
   adoção: hardware nunca testado, sem `.exe`, TXT não validado; 🟠 metrologia: sync tensão×strain,
   aferição sem captura ao vivo, correlação sem alerta; 🟡 paridade/robustez: FFT ao vivo, longa
   duração).
2. **Backlog permanente** → `docs/tarefas-futuras.md` ganhou a seção **"Urgências para a adoção
   (Fase 5–6)"** consolidando os gaps; a seção "Outras" foi enxugada (sem duplicação).
3. **Guia de campo unificado** → `docs/guia-teste-hardware.md` (novo): do ambiente zerado ao ensaio
   validado **no hardware real do tio**, com checklist e troubleshooting; o caso simulado virou
   variante 🧪. **Fundiu e apagou** `guia-windows.md` + `validacao-windows.md`. Ponteiros corrigidos
   em CLAUDE.md, uso.md, ADR-007/009/014 e contexto-hardware §8.
4. **Auditoria de defasagem** (a pedido do Weslley): corrigidos roadmap (a **Fase 4 estava listada em
   "Fases que faltam"** — movida para "concluídas"; data 25→28/06), contexto-hardware §8 ("Fase 4 é a
   próxima" → "Fases 0–4 concluídas") e o README (105→178 testes, 14→18 ADRs, "dashboard em
   construção" → pronto).
5. **README como vitrine** → reescrito: abre em **O problema → A solução** (+ autoria solo), Status
   reenquadrado como "próximos passos", estrutura com `apresentacao/`, e **três mídias**:
   - `.github/assets/dashboard.gif` — o dashboard **ao vivo** (convertido de um `.mov` do Weslley via
     ffmpeg, 900px/10fps, 3,7 MB) — **imagem-herói**.
   - `.github/assets/afericao.png` — a tela de aferição (correlação 99,98%).
   - `.github/assets/testes.png` — 178 testes passando (substituiu a antiga que mostrava 105),
     exibida pequena (`width=380`).

     Tudo consolidado em **`.github/assets/`** (padrão profissional escolhido pelo Weslley); a pasta
     `docs/assets/` foi removida.
6. **ADR-019 (Aceito)** — registra a **decisão de direção** (priorizar hardware/`.exe`/TXT sobre
   features no Mac) e a reorganização da documentação. Índice de ADRs, CHANGELOG e CLAUDE.md
   (range `adr/001…019`, árvore) atualizados.
7. **Texto do "About" do GitHub** entregue na conversa (PT + EN + topics) — o Weslley aplica
   manualmente (não é arquivo do repo).

## 4. Estado atual

- **178 testes verdes** (`uv run pytest`) — nenhuma mudança de código.
- Documentação coerente: zero defasagem residual (auditada por grep), todos os links de imagem do
  README resolvem, numeração de fases unificada.
- **Working tree** com a sessão inteira commitada; **PR `develop → main` aberta**.

## 5. Bloqueios e dependências

- **Merge `develop → main` é do Weslley.**
- **As três urgências 🔴 dependem do hardware/Windows do tio** — fora do Mac. Não há como exercê-las
  daqui.
- **`docs/avaliacao-critica.md` é temporário** — pode ser removido quando as urgências fecharem (o
  registro permanente é `tarefas-futuras.md`).

## 6. Próximos passos (em ordem de valor — ver [ADR-019](../adr/019-foco-em-validacao-fisica-e-adocao.md))

1. **Fase 5 — validação física no hardware do tio** (a frente de maior valor; exige Windows +
   hardware, não dá no Mac): seguir [guia-teste-hardware.md](../guia-teste-hardware.md) — chassi no
   NI-MAX → test panel como gabarito → mapear canais reais → **bater a leitura** → calibrar a
   extensometria de verdade → validar o **TXT** no AqAnalysis dele.
2. **Fase 6 — empacotar um `.exe`** (PyInstaller) e pôr na mão do tio. Sem isso, adoção = 0.
3. **Refinamentos no Mac (se ficar no Mac antes da Fase 5):** **capturar a leitura ao vivo na
   aferição** (hoje a tensão é digitada — gap 🟠5), **alerta de correlação baixa** (🟠6). São os dois
   que mais aproximam o fluxo do tio sem depender de hardware.
4. **Quando chegar a vibração:** o **ADR-árbitro de FFT ao vivo vs. exportar pro AqAnalysis** (🟡7).

## 7. Artefatos relevantes

- **Decisão da sessão:** [ADR-019](../adr/019-foco-em-validacao-fisica-e-adocao.md).
- **Avaliação e backlog:** [avaliacao-critica.md](../avaliacao-critica.md) (temporário),
  [tarefas-futuras.md](../tarefas-futuras.md) §Urgências (permanente).
- **Guia de campo:** [guia-teste-hardware.md](../guia-teste-hardware.md).
- **Vitrine:** [README.md](../../README.md) + `.github/assets/{dashboard.gif,afericao.png,testes.png}`.
- **Comandos úteis:**
  - `uv run pytest` → **178 passed**.
  - Print novo dos testes: `clear && uv run pytest`.
  - Abrir o dashboard (Mac): `PYTHONPATH=src uv run python -m ensaios_ni.apresentacao.qt.janela`.
  - Recriar o GIF de um `.mov` (two-pass, palette):
    `ffmpeg -i in.mov -vf "fps=10,scale=900:-1:flags=lanczos,palettegen=stats_mode=diff" pal.png` e
    `ffmpeg -i in.mov -i pal.png -lavfi "fps=10,scale=900:-1:flags=lanczos,paletteuse" out.gif`.

## 8. Como iniciar a próxima sessão

1. Confirmar com o Weslley se a **PR `develop → main` foi mergeada**; se sim, sincronizar a `develop`.
2. Ler **este handoff** + [roadmap.md](../roadmap.md) + [ADR-019](../adr/019-foco-em-validacao-fisica-e-adocao.md).
   Para a Fase 5, ler também [guia-teste-hardware.md](../guia-teste-hardware.md) e
   [contexto-hardware.md](../contexto-hardware.md) (API pinada do `nidaqmx`, armadilha do strain).
3. `uv run pytest` → **178 passed** (confirma a base).
4. **Decidir a frente:** Fase 5 exige o **Windows + hardware do tio**; no Mac, atacar os refinamentos
   🟠5/🟠6 da aferição.
5. Regras de sempre: `import nidaqmx` só em `daqmx.py` (lazy); `import PySide6` só em
   `apresentacao/qt/`; strain nunca usa os defaults da API; português em tudo; commits separados por
   camada; **nada de commit/push/merge autônomo**.
