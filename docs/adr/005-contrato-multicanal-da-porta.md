# ADR 005 — Contrato multi-canal da porta e adaptador DAQmx de tensão

## Status

Aceito — **validado no Windows** com dispositivos simulados do NI-MAX em 22/06/2026 (Python 3.12.10, `nidaqmx` 1.5.0): o `daqmx` leu os 9205 simulados via CLI sem erro, com DIFF e sample clock funcionando. Validação quantitativa contra o test panel fica para o hardware real (Fase 4).

## Contexto

O [ADR-001](001-arquitetura-porta-adaptador.md) e o [ADR-002](002-conversao-linear-e-contrato-da-porta.md)
deixaram explicitamente pendente, "para quando a Fase 2 começar", **como a porta lida com
timing/sample clock** e **se a leitura é por canal ou por task**. A porta original lia um canal
por vez, sem taxa: `ler_tensao(canal, amostras) -> list[float]`.

Dois fatos forçam a decisão agora:

1. **A validação no Windows (22/06/2026) descobriu que o 9235 (delta-sigma) no chassi
   cDAQ-9184 (Ethernet) falha com leitura on-demand** — exige `cfg_samp_clk_timing` explícito.
   Os 9205 toleram on-demand, mas o timing passa a ser obrigatório por consistência.
2. **Os ensaios do dono do hardware cruzam canais no tempo:** prova de carga gera
   carga × deformação, e vibração (1024 Hz) vira FFT. Ambos exigem que os canais sejam
   amostrados pelo **mesmo sample clock**, alinhados no tempo. Ler canal-a-canal, em tasks
   separadas, perde esse alinhamento.

## Decisão

- **A porta passa a ler por task, multi-canal, com taxa:**
  `ler_tensao(canais: list[str], amostras: int, taxa_hz: float) -> dict[str, list[float]]`.
  Uma chamada lê todos os canais de uma task sob o mesmo sample clock. Continua devolvendo
  **volts brutos** — o ADR-002 segue valendo (conversão é do domínio).
- **Adaptador real `aquisicao/daqmx.py`** (só tensão/9205 nesta fatia): monta a task,
  `add_ai_voltage_chan` por canal (DIFF, ±10 V por padrão), `cfg_samp_clk_timing` e `task.read`,
  e **normaliza** o retorno do `read` (lista simples para 1 canal, lista de listas para vários)
  num `dict[canal -> list]`. Import `nidaqmx` **lazy**, só neste arquivo.
- **Aquisição finita para o MVP:** `sample_mode=FINITE` + `samps_per_chan=amostras`. Streaming
  contínuo (callback / `register_every_n_samples...`) fica para evolução posterior.
- **Teste no Mac por mock de `nidaqmx`** (injeção em `sys.modules`): verifica os parâmetros das
  chamadas, em especial que `cfg_samp_clk_timing` é **sempre** chamado (guarda contra regressão
  pro on-demand). O strain (9235) fica fora desta fatia — espera o gage factor do dono.
- **Ponto de entrada de produção** (`python -m ensaios_ni`) ganha `argparse`:
  `--fonte {fake,daqmx}`, `--config`, `--taxa`, `--amostras`, `--saida` — resolvendo o
  "pendente" do [ADR-004](004-camada-de-aplicacao-e-ponto-de-entrada.md).

## Consequências

**Melhora:**

- Canais alinhados no tempo — carga × deformação e FFT ficam corretos.
- O `cfg_samp_clk_timing` obrigatório evita o erro silencioso de on-demand no chassi Ethernet.
- O caso de uso `executar_ensaio` não mudou de forma: só passou a chamar a porta uma vez com a
  lista de canais. Trocar `fake` por `daqmx` continua sendo a única diferença Mac↔Windows.

**Piora / pendente:**

- O mock prova que chamamos a API como esperado, **não** que a API real aceita as chamadas. A
  validação objetiva continua sendo no Windows, contra o **test panel do NI-MAX** (ADR-001).
- **Strain (9235) ainda não tem leitura** — entra numa fatia seguinte, com o gage factor do
  dono. A porta provavelmente ganhará um caminho próprio para strain (ou um método irmão).
- Aquisição é **finita** (lê N amostras e para). Ensaios longos / contínuos exigirão streaming.
