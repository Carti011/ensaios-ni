# Handoff: Fase 2 (aquisição de tensão) + respostas do tio e replanejamento

**Data:** 2026-06-22
**Status:** Fase 2 (tensão) pronta e testada no Mac; **PR #2 aberta** (develop→main) aguardando validação no Windows e merge do Weslley. Rodada 2 do tio respondida — replanejamento feito (ADRs 005/006/007).

## 1. Objetivo

Substituir LabVIEW/FlexLogger (pagos) por software próprio em Python sobre o driver gratuito
NI-DAQmx, para o hardware do tio do Weslley (OFM Engenharia: chassi cDAQ-9184 + 2× NI 9205 de
tensão + 1× NI 9235 de strain). Esta sessão entregou a **leitura de tensão ponta a ponta** e,
sobretudo, **destravou o domínio** com as respostas do dono do hardware.

## 2. O que foi feito nesta sessão

**Código (Fase 2 — tensão), TDD, 22→30 testes verdes, em 5 commits na `develop`:**

- **Contrato da porta multi-canal** ([porta.py](../../src/ensaios_ni/aquisicao/porta.py)):
  `ler_tensao(canais, amostras, taxa_hz) -> dict[str, list[float]]`. Lê todos os canais numa task
  sob o mesmo sample clock (alinhados no tempo — necessário pra carga×deformação e FFT). Fake e
  `executar_ensaio` adaptados.
- **Adaptador real** ([daqmx.py](../../src/ensaios_ni/aquisicao/daqmx.py)) para tensão (9205):
  monta task, `cfg_samp_clk_timing` explícito, `task.read`, normaliza em dict. Import `nidaqmx`
  **lazy**, só nesse arquivo. Testado no Mac via **mock do nidaqmx em `sys.modules`** (inclui teste
  que garante que o sample clock é sempre configurado — anti-regressão pro on-demand).
- **CLI de produção** ([__main__.py](../../src/ensaios_ni/__main__.py)):
  `python -m ensaios_ni --fonte {fake,daqmx} --config --taxa --amostras --saida`.
- **ADR-005**, README e CHANGELOG atualizados.

**Validação do ambiente Windows (Fases 0 e 1 fechadas):** NI-MAX com simulados (`cDAQ1` +
`cDAQ1Mod1`/`Mod2` = 9205, `cDAQ1Mod3` = 9235); `nidaqmx` lendo os 3. **Descoberta:** o 9235
(delta-sigma) **falha em leitura on-demand no chassi Ethernet** — exige `cfg_samp_clk_timing`. O
120 Ω quarter-bridge foi confirmado pela etiqueta física.

**Respostas do tio (2 áudios transcritos com `mlx-whisper large-v3-turbo`) — rodada 2 respondida.**
Detalhe em [respostas-tio.md](../respostas-tio.md). Pontos que mudaram o plano:

- **Conversão NÃO é linear fixa.** O tio faz **calibração empírica por pontos + tara/null** (estilo
  AqDados/Lynx). → revisa o ADR-002, vira **ADR-006**.
- **Duração de 1 h a 1 ano contínuo** → aquisição contínua, **ADR-007** (hoje é finita).
- **Gage factor 2,14–2,16** (varia, configurável); strain com **3 fios** (cabo longo); strain em
  **microstrain**.
- **9205:** LVDT (deslocamento) e acelerômetro (5 V externos); vibração com acelerômetro 2G a 1024
  Hz; célula de carga em dúvida (precisa de saída em tensão).
- **Grátis×pago esclarecido:** o pago é só o **FlexLogger**; NI-DAQmx + NI-MAX são grátis. Nosso
  software substitui o FlexLogger — o tio **não precisa pagar nada**.
- **Softwares do tio:** AqDados (aquisição/calibração) e AqDAnalysis (análise tempo/frequência) —
  compatibilizar formato é meta.
- **IP fixo do chassi:** registrado **só no cofre privado** (`~/cofre/01-projetos/ensaios-ni.md`),
  fora do repo.

**Docs replanejadas:** ADR-002 marcado como estendido; **ADR-006** (calibração por pontos) e
**ADR-007** (aquisição contínua) criados em estado *Proposto*; `contexto-hardware.md §6`,
`CONTEXT.md` (glossário) e o brief do cofre atualizados.

## 3. Estado atual

- **30 testes verdes** (`uv run pytest`) no Mac, sem `nidaqmx`. Teste-guarda de arquitetura verde.
- **`develop` pushada; PR #2** (develop→main) aberta com descrição completa:
  https://github.com/Carti011/ensaios-ni/pull/2
- Código: `dominio/` (canais, conversão, erros), `aquisicao/` (porta, fake, **daqmx**),
  `persistencia/` (csv), `aplicacao/` (ensaio, demo), `__main__.py` (CLI).
- ADRs 001–007 (006 e 007 em *Proposto*). Glossário e contexto-hardware refletem a rodada 2.

## 4. Bloqueios e dependências

- **Validação no Windows pendente (próximo passo nº 1).** O `daqmx` de tensão só foi testado por
  mock no Mac. Critério objetivo de "funcionou" = bater com o **test panel do NI-MAX** no mesmo
  canal. O Weslley faz: `git pull` no Windows → branch `develop` → testar → se ok, **merge da PR #2**
  (o merge é dele; nunca autônomo).
- **Rodada 3 de perguntas ao tio** (reservada em [respostas-tio.md](../respostas-tio.md)): fiação
  do 9205 (diff/SE), célula de carga, sensibilidades/faixas dos sensores, taxa dos ensaios lentos,
  formato de arquivo p/ AqDados/AqDAnalysis, modelo do acelerômetro.

## 5. Próximos passos (roadmap)

1. **Validar tensão no Windows** contra o NI-MAX (fecha a Fase 2 de tensão). ← decidido como a 1ª fatia.
2. **Calibração por pontos + tara** ([ADR-006](../adr/006-calibracao-por-pontos.md)) — faz o número
   virar grandeza física real; estilo AqDados. Revisa o ADR-002.
3. **Strain do 9235**: quarter-bridge 120 Ω, **3 fios**, gage factor 2,14–2,16, microstrain, null.
4. **Aquisição contínua** ([ADR-007](../adr/007-aquisicao-continua.md)) — monitoramento de longa duração.
5. **Análise/FFT** (estilo AqDAnalysis) — não depende do tio, só os números reais dependem.
6. **Dashboard** (Fase 3) — vira ADR de escolha de stack.

## 6. Como iniciar a próxima sessão (no Mac)

1. Ler este handoff, `CLAUDE.md`, `CONTEXT.md` e os ADRs 005/006/007.
2. `uv run pytest` → **30 passed**. Se não, recriar o venv (`uv venv --python 3.12`).
3. Confirmar com o Weslley se a **PR #2 foi mergeada** (validação no Windows). Se sim, a Fase 2 de
   tensão está fechada → atacar a **calibração por pontos** (ADR-006) via TDD no domínio, ou o que o
   Weslley priorizar do roadmap.
4. Manter as regras: import `nidaqmx` só no `daqmx.py` (lazy); teste-guarda verde; commits separados
   por camada; nada de commit/push/merge autônomo; português em tudo.
