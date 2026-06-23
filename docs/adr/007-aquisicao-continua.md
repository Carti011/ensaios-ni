# ADR 007 — Aquisição contínua de longa duração

## Status

Proposto

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

## Consequências

**Melhora:**

- Cobre o uso real (monitoramento de meses), não só a captura curta.
- Gravação incremental protege contra perda de dados em ensaios longos.

**Piora / pendente:**

- Mais complexidade: buffers, callbacks, gravação concorrente, rotação de arquivo.
- Reabre a escolha de **formato de persistência** (CSV append vs TDMS) sob alta taxa/volume.
- A porta passa a ter dois modos (finito e streaming) — manter a interface enxuta exige cuidado.
- Só validável de verdade no Windows (e, no limite, no hardware com ensaio longo real).
