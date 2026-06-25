# ADR 007 — Aquisição contínua de longa duração

## Status

**Aceito — implementado e validado no Windows simulado em 25/06/2026.** Testável no Mac via fake;
no Windows (NI-MAX simulado) o `daqmx` rodou os modos finito e contínuo (tensão + strain) sem erro,
com tempo contínuo e encerramento limpo por duração e por Ctrl-C. O **número físico** do strain fica
para o hardware (Fase 4). Implementação descrita abaixo; registro da validação em
[validacao-windows.md](../validacao-windows.md).

## Contexto

O [ADR-005](005-contrato-multicanal-da-porta.md) entregou a leitura **finita**: a task lê N
amostras (`sample_mode=FINITE`, `task.read`) e para. Foi o suficiente para a fatia de tensão e
para validar o caminho.

As respostas do dono (22/06/2026, [respostas-tio.md](../respostas-tio.md)) mostram que a
duração real dos ensaios vai de **uma hora a um mês contínuo, ou até um ano** (monitoramento de
estruturas), além de provas de carga de 24 h. Ler N amostras e parar não cobre isso: precisamos
de **aquisição contínua**, com gravação incremental, sem estourar memória nem perder amostras.

## Decisão

Adotar **aquisição contínua** para os ensaios de monitoramento (decisão de direção; detalhes na
implementação):

- Task em `sample_mode=CONTINUOUS` com leitura por blocos — via
  `register_every_n_samples_acquired_into_buffer_event(N, callback)` ou
  `nidaqmx.stream_readers` para throughput maior (ambos pinados em
  [contexto-hardware.md §4](../contexto-hardware.md)).
- **Gravação incremental** (append) no CSV a cada bloco, em vez de acumular tudo em memória.
  Avaliar **rotação de arquivo** (por tempo/tamanho) e migração para **TDMS** (binário nativo
  NI) se o CSV não der conta da taxa/volume.
- A porta `FonteDeAquisicao` ganha um modo de **streaming** (ex.: um gerador/callback de blocos)
  além do `ler_tensao` finito atual. O `fake` simula blocos para manter o TDD no Mac.
- Encerramento limpo (parar a task, fechar arquivo) e robustez a falhas de rede do chassi
  Ethernet em ensaios longos.

## Implementação (25/06/2026)

- **Porta:** dois métodos de streaming irmãos dos finitos — `transmitir_tensao` e `transmitir_strain`
  (`canais, taxa_hz, amostras_por_bloco) -> Iterator[dict]`. Cada um é um **gerador de blocos**.
  O `fake` fatia listas sintéticas em blocos (TDD no Mac); o `daqmx` usa `sample_mode=CONTINUOUS` +
  `task.read` por bloco num laço, com a task fechada ao encerrar o gerador (encerramento limpo).
- **Persistência incremental:** classe `GravadorEnsaioCsv` (context manager) escreve o cabeçalho uma
  vez e cada bloco em append, mantendo o `tempo_s` **contínuo** entre blocos (índice de amostra
  global). O `gravar_ensaio` finito virou o caso de um único bloco dela (sem duplicação).
- **Caso de uso `executar_ensaio_continuo`:** captura a tara no início (leitura finita curta), abre
  um fluxo por tipo presente e **costura tensão+strain bloco a bloco** (`zip` dos geradores),
  convertendo e gravando incrementalmente.
- **Encerramento:** por **`duracao_s`** (arredondado ao bloco) e/ou por **interrupção** — um callback
  `parar` consultado a cada bloco, que a CLI liga ao **Ctrl-C** (SIGINT), sempre gravando o bloco
  corrente antes de sair.
- **CLI:** `--continuo`, `--duracao-s`, `--bloco`. No `fake` gera sinal sintético cobrindo a duração;
  no `daqmx` exige `--config`.

## Consequências

**Melhora:**

- Cobre o uso real (monitoramento de meses), não só a captura curta.
- Gravação incremental protege contra perda de dados em ensaios longos.

**Piora / pendente:**

- A porta passa a ter dois modos (finito e streaming) — manter a interface enxuta exige cuidado.
- **Só validável de verdade no Windows** (e, no limite, no hardware com ensaio longo real). O mock
  prova que montamos a task em `CONTINUOUS` e encerramos limpo, não que o streaming real não perde
  amostras. Runbook em [validacao-windows.md](../validacao-windows.md).
- **Sincronização das duas tasks contínuas (tensão e strain)** segue pendente — é a mesma pendência
  de **start-trigger** do [ADR-009](009-leitura-de-strain-9235.md). No `zip` dos geradores há um
  pequeno offset entre os tipos; alinhamento fino exige trigger compartilhado, validável só no Windows.
- **Rotação de arquivo** (por tempo/tamanho) e migração para **TDMS** sob alta taxa/volume **não
  foram feitas** — entram quando um ensaio longo real mostrar que o CSV append não dá conta.
- Robustez a **quedas de rede** do chassi Ethernet em ensaios de meses ainda não tratada.
