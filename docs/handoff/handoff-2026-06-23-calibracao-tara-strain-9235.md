# Handoff: calibração por pontos, tara e leitura de strain do 9235

**Data:** 2026-06-23
**Status:** aguardando decisão (PR #3 develop→main aberta — o Weslley faz o merge no GitHub). Backend de aquisição completo até strain; próximo é integrar tensão+strain no fluxo.

## 1. Objetivo

Substituir LabVIEW/FlexLogger (pagos) por software próprio em Python sobre o driver gratuito NI-DAQmx, para o hardware do tio do Weslley (OFM Engenharia: cDAQ-9184 + 2× NI 9205 de tensão + 1× NI 9235 de strain). Esta sessão completou o **domínio de conversão** (calibração por pontos + tara) e a **leitura de strain do 9235** — a parte de maior risco técnico —, sob o norte de **paridade com o FlexLogger**.

## 2. Contexto essencial

- **Stack:** Python 3.12, `pytest`, `uv` (Mac). `nidaqmx` é extra opcional `[hardware]`, só Windows/Linux x86. **Não roda em macOS/ARM.**
- **Arquitetura porta/adaptador** (ADR-001): porta `FonteDeAquisicao`; adaptador `daqmx` (real, único que importa `nidaqmx`, lazy) e `fake` (sintético, Mac). ~90% testável no Mac.
- **Norte de design — paridade com o FlexLogger** (ADR-008): o tio já usa o FlexLogger e só não quer pagar. Como o FlexLogger usa as Custom Scales do NI-DAQmx por baixo, "parecer com o FlexLogger" == "seguir o padrão NI". **Regra operacional: em dúvida, pesquisar como o FlexLogger resolve antes de inventar** (ver `docs/referencia-flexlogger.md`).
- **Armadilha do strain (a maior do projeto):** os defaults de `add_ai_strain_gage_chan` são full-bridge 350 Ω / 2,5 V; o 9235 é quarter-bridge 120 Ω / 2,0 V. Rodar com defaults dá número plausível e errado, sem erro.
- **Perguntas ao tio ENCERRADAS** (decisão do Weslley, 23/06): o que faltar segue boas práticas pesquisadas; novas perguntas só quando surgir necessidade.

## 3. O que já foi feito (nesta sessão)

**Código (TDD, red→green→refactor; 30 → 53 testes verdes):**

- **Calibração por pontos** (`dominio/conversao.py`, `canais.py`): `converter()` aceita `pontos=[[volts,valor]]` por canal, interpola linear por segmento e faz **clamp** fora da faixa (= Table scale do DAQmx). `ganho/offset` linear continua como fallback. Config valida pontos (≥2, ordenados, volts distintos) ou linear.
- **Tara (zero)**: `calcular_tara(amostras, canal)` = média do repouso na unidade; `converter(..., tara=)` subtrai. Integrada ao `executar_ensaio(..., amostras_tara=)` e à CLI (`--amostras-tara`). Replica o "Zero Channel" do FlexLogger. Em repouso a leitura tarada é zero mesmo com escala deslocada.
- **Strain do 9235**: porta ganhou `ler_strain` (abstrato; task separada; devolve strain adimensional). `ConfigStrain` (dataclass em `daqmx.py`) com defaults SEGUROS do 9235. `AdaptadorDaqmx.ler_strain` usa `add_ai_strain_gage_chan` + sample clock obrigatório. **Teste-guarda anti-armadilha** trava quarter-bridge/120/2,0. microstrain = canal linear ganho 1.000.000 (reusa o domínio).

**Pesquisa e docs:**

- **Estudo de mercado** (FlexLogger/NI/Lynx + site OFM) respondeu 7 das 10 perguntas pendentes — ver `docs/referencia-flexlogger.md §5`. Descoberta-chave: **AqDAnalysis não importa CSV de terceiros** (só formatos proprietários) → não perseguir compatibilidade de arquivo; gerar CSV legível.
- **ADRs criados:** ADR-006 (calibração por pontos, promovido a Aceito), ADR-008 (paridade FlexLogger), ADR-009 (leitura de strain).
- **Respostas do tio (parcial):** "tá tudo certo" (valida diferencial, clamp, tara, célula com condicionador) + **taxa estático 20 Hz** + acelerômetro **Dytran 7523A1** (550 mV/g, ±2g, 0–1500 Hz, 5 V DC, triaxial DC/capacitivo → canal de tensão, ganho ≈ 1,818 g/V).

**Git:** 6 commits na `develop` (chore gitignore; feat calibração; docs paridade; feat tara; feat strain; docs estudo/ADR-009). PR #3 aberta com descrição completa.

## 4. Estado atual

- **53 testes verdes** no Mac (`uv run pytest`), sem `nidaqmx`. Teste-guarda de arquitetura verde (`nidaqmx` só no `daqmx.py`).
- **Funciona:** porta multi-canal (`ler_tensao` + `ler_strain`), fake e daqmx, conversão pontos/linear, tara, CSV, CLI.
- **Incompleto (próxima fatia):** o `executar_ensaio`/CLI **só lê tensão** — `ler_strain` existe mas não está no fluxo de produção. Por isso **não vale ir ao Windows ainda** (veria o mesmo da Fase 2).
- **PR #3** develop→main aberta: <https://github.com/Carti011/ensaios-ni/pull/3> — aguardando merge manual do Weslley.

## 5. Bloqueios e dependências

- **Merge da PR #3**: o Weslley faz no GitHub.
- **Validação real do strain/tensão**: só no Windows (simulado) e depois no hardware do tio, contra o test panel do NI-MAX. O mock prova que montamos a task certo, não que o número físico bate.
- Nenhum bloqueio de informação: perguntas ao tio encerradas; o que falta segue boas práticas.

## 6. Próximos passos (roadmap, em ordem)

1. **Integrar tensão + strain no `executar_ensaio`/CLI**: escolher o tipo de cada canal (tensão vs strain) e gravar tudo num ensaio. Após isso, **ida ao Windows** mostra o 9235 simulado gerando microstrain (primeira evolução visível nova).
2. **Aquisição contínua** de longa duração (ADR-007): hoje é finita (lê N e para); ensaios de horas/meses exigem streaming + gravação incremental.
3. **Análise/FFT** (estilo AqDAnalysis) — substituímos o FlexLogger, a análise é nossa daqui pra frente.
4. **Dashboard** (Fase 3) — vira ADR de escolha de stack.
5. **Validação no hardware do tio** (Fase 4) — quando o Weslley for à casa dele.

## 7. Artefatos relevantes

- Código: `src/ensaios_ni/aquisicao/{porta,fake,daqmx}.py`, `dominio/{conversao,canais}.py`, `aplicacao/ensaio.py`, `__main__.py`.
- Decisões: `docs/adr/006`, `008`, `009`; `docs/referencia-flexlogger.md`; `docs/respostas-tio.md`.
- API do `nidaqmx` pinada: `docs/contexto-hardware.md §4`.
- Conversão do acelerômetro real: ganho ≈ **1,818 g/V** (Dytran 7523A1, 550 mV/g) — canal de tensão.
- `ConfigStrain` (defaults do 9235): `gage_factor=2.15`, `nominal_gage_resistance=120.0`, `voltage_excit_val=2.0`, `bridge_config="QUARTER_BRIDGE_I"`.
- Comandos:
  - `uv run pytest` → 53 passed.
  - Demo: `PYTHONPATH=src uv run python -m ensaios_ni`.

## 8. Como iniciar a próxima sessão (no Mac)

1. Ler este handoff, `CLAUDE.md`, `CONTEXT.md`, e os ADRs 006/008/009.
2. `uv run pytest` → **53 passed**. Se não, recriar venv (`uv venv --python 3.12`).
3. Confirmar com o Weslley se a **PR #3 foi mergeada**.
4. Atacar a **fatia 1 do roadmap**: integrar tensão+strain no `executar_ensaio`/CLI, via TDD. Decisão de design a fechar no início: como o config diferencia canal de tensão de canal de strain (ex.: campo `tipo`/`modulo` no `canais.toml`, ou listas separadas) e como uma execução grava os dois (tasks separadas, alinhadas no tempo).
5. Regras: import `nidaqmx` só no `daqmx.py` (lazy); teste-guarda verde; strain nunca usa defaults da API; commits separados por camada; nada de commit/push/merge autônomo; português em tudo.
