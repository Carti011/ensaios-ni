# ADR 018 — Metadata do ensaio em arquivo paralelo (Fase 4, fatia 4)

## Status

**Aceito** (27/06/2026). Implementa a parte de **metadata** da fatia 4 do plano do
[ADR-015](015-ux-e-fluxo-do-dashboard.md). Não altera a persistência do ensaio em si
([ADR-003](003-persistencia-csv-do-ensaio.md)) nem os exportadores ([ADR-012](012-serie-temporal-e-exportadores.md));
acrescenta um arquivo de metadata ao lado do CSV e o repassa aos exportadores.

## Contexto

O ensaio do tio vira **laudo** — documento técnico/legal que exige **rastreabilidade**: obra, data,
responsável, observação. O relatório do AqDAnalysis ([referencia-lynx §2.4](../referencia-lynx.md))
carrega exatamente esses campos. O [ADR-015](015-ux-e-fluxo-do-dashboard.md) previu metadata no topo
do dashboard, mas deixou em aberto **onde ela é persistida**.

O CSV de gravação é **só dados**, no layout "wide" do [ADR-003](003-persistencia-csv-do-ensaio.md)
(`tempo_s` + uma coluna por canal), e o `carregar_csv` ([ADR-012](012-serie-temporal-e-exportadores.md))
depende desse layout. Embutir metadata no topo do CSV sujaria o formato e quebraria o leitor.

## Decisão

- **Arquivo paralelo `<ensaio>.meta.toml`**, ao lado do CSV (`ensaio.csv` ↔ `ensaio.meta.toml`).
  O ensaio vira um **par**: dados + metadata, cada um no seu arquivo. O CSV e o `carregar_csv`
  ficam intactos.
- **Value object `Metadata`** no domínio (`dominio/metadata.py`): campos **obra, operador, data,
  observacao** (strings, todos opcionais/`""`), espelhando o relatório do AqDAnalysis. Imutável,
  sem dependência de I/O.
- **Persistência** em `persistencia/metadata_ensaio.py`: `gravar_metadata(caminho_csv, metadata)`
  escreve a seção `[ensaio]` no `.meta.toml` (via `tomlkit`); `ler_metadata(caminho_csv)` devolve a
  `Metadata` (ou uma vazia se o arquivo não existe). O caminho do `.meta.toml` é derivado do CSV
  (`with_suffix(".meta.toml")`).
- **UI**: campos de metadata no topo do workspace (layout do ADR-015). Ao **gravar** o ensaio
  (Parar), o dashboard salva o `.meta.toml` ao lado do CSV.
- **Exportadores**: recebem a `Metadata` (opcional) e, quando presente, **carimbam um cabeçalho de
  rastreabilidade** no arquivo exportado (o laudo). Vale para os formatos **de leitura**
  (`csv-excel-br`, `xlsx`). O **`txt-aqanalysis` fica de fora** por ora — o layout do "Importa
  Arquivo Texto" é sensível e ainda provisório ([ADR-011](011-estrategia-de-exportacao.md)); metadata
  no topo atrapalharia a importação.

## Consequências

**Melhora:**

- Rastreabilidade do laudo sem tocar no formato de dados — CSV e leitor intactos.
- A metadata **persiste com o ensaio**: reexportar (outra janela/formato) mantém o cabeçalho sem
  redigitar.
- Campos espelham o que o tio já vê no relatório do AqDAnalysis.

**Piora / pendente:**

- O ensaio passa a ser **dois arquivos** (mover/copiar exige levar o par junto).
- Conjunto de campos **fixo** no MVP (obra/operador/data/observacao); expandir (instituição,
  documento de referência) é aditivo, quando o tio pedir.
- O **`txt-aqanalysis` não leva metadata** até o layout de importação ser validado (Fase 5).
- A **data** é um campo de texto preenchido na UI (pré-carregada com a data atual), não um timestamp
  de hardware — coerente com o resto (o tempo do ensaio já vem da taxa, não do relógio).
