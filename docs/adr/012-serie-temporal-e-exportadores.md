# ADR 012 — Série temporal como value object e exportadores que partem dela

## Status

Aceito (25/06/2026). Detalha a "camada de exportadores plugáveis" do
[ADR-011](011-estrategia-de-exportacao.md).

## Contexto

O [ADR-011](011-estrategia-de-exportacao.md) decidiu **não reescrever a análise** (fica no
AqDAnalysis do dono) e entregar **exportadores plugáveis** a partir da "mesma série temporal em
memória": CSV legível (já existe), **CSV amigável ao Excel BR** (`;` + decimal vírgula), **`.xlsx`**
nativo (via `openpyxl`) e, depois, **TXT** para o AqDAnalysis (layout ainda incógnito).

Faltava decidir **de onde o exportador lê os dados**. Duas opções:

- **Da memória do ensaio finito** — o `dict[str, list[float]]` que sobra de `executar_ensaio`.
  Simples, mas **não cobre o ensaio contínuo** (ADR-007), que por design **não acumula em memória** —
  grava o CSV em append, bloco a bloco. Também não permite **reexportar** um ensaio já salvo.
- **De uma série temporal carregável** — um value object que tanto vem da memória (ensaio finito)
  quanto de um **CSV já gravado** (`carregar_csv`). Cobre finito, contínuo e reexportação.

O fluxo real do dono é "**gravou, depois quer no Excel / mandar pro AqDAnalysis**" — muitas vezes
sobre um ensaio antigo, não no calor da aquisição. Exportar só da memória deixaria de fora justamente
o caso de uso principal.

## Decisão

- **`SerieTemporal` é um value object** (`dominio/serie.py`): `canais` (ordem), `unidades`
  (`canal -> unidade`), `taxa_hz` e `dados` (`canal -> list[float]`). Imutável, sem dependência de
  aquisição nem de `nidaqmx`. Carrega as mesmas invariantes da persistência (taxa > 0, todos os
  canais com o mesmo número de amostras). É a **moeda comum** entre quem produz o ensaio e quem
  exporta.
- **`carregar_csv(caminho) -> SerieTemporal`** (`persistencia/csv_ensaio.py`): lê o CSV "wide" do
  [ADR-003](003-persistencia-csv-do-ensaio.md) (coluna `tempo_s` + uma por canal), reconstrói as
  unidades a partir do cabeçalho `Canal (unidade)` e **deriva a `taxa_hz` do `tempo_s`**. É o inverso
  de `gravar_ensaio`. Desacopla a exportação do fluxo de aquisição e habilita reexportar ensaios
  antigos.
- **Exportadores partem da `SerieTemporal`**, não do `dict` cru. Cada formato é uma rotina
  independente em `persistencia/exportadores/`, com a assinatura comum
  `exportar(serie, caminho, sinais=None)`:
  - **`csv_excel_br`** — separador `;` e **decimal com vírgula**, sem depender de `locale` (frágil,
    é estado global): formata cada número trocando `.` por `,` explicitamente. Sem dependência nova.
  - **`xlsx`** — via **`openpyxl`**, **import lazy** dentro da função (o pacote tem que importar no
    Mac mesmo sem `openpyxl`). Extra opcional **`[excel]`** no `pyproject`; incluído no grupo `dev`
    para rodar o TDD no Mac (`openpyxl` é Python puro, roda em ARM).
  - **`txt` (AqDAnalysis)** — adiada até o layout estar fechado (bloqueio do ADR-011).
- **Seletividade de sinais.** O parâmetro `sinais: list[str] | None` filtra **quais canais** entram
  no arquivo (preservando a ordem do config); `None` = todos. Atende o pedido do dono ("nem todos são
  importantes colocar lá"). A coluna `tempo_s` é sempre incluída.
- **CSV legível atual permanece** como gravação primária (inclusive incremental no contínuo). Os
  exportadores são um **passo pós-ensaio**, sob demanda, sobre uma `SerieTemporal`.

## Consequências

**Melhora:**

- Um único contrato (`SerieTemporal`) para todos os exportadores; adicionar formato não toca no
  domínio nem na aquisição.
- Cobre os três fluxos: exportar logo após o ensaio finito, exportar um ensaio **contínuo** (lendo o
  CSV gravado) e **reexportar** um CSV antigo.
- `carregar_csv` é testável 100% no Mac e vira a base do dashboard da Fase 3 (carregar e visualizar).

**Piora / pendente:**

- `carregar_csv` **assume o layout wide do ADR-003** e amostragem uniforme (deriva a taxa de duas
  primeiras linhas de `tempo_s`). Se algum dia houver timestamp não uniforme, revisar.
- O `.xlsx` adiciona `openpyxl` (opcional). Para arquivos muito longos, `openpyxl` carrega tudo em
  memória — aceitável para os ensaios atuais; se um dia houver ensaio gigante, usar `write_only` ou
  manter no CSV.
- A `SerieTemporal` carrega o ensaio **inteiro** em memória ao reexportar — não serve para um
  contínuo de horas. Para esse caso, exportação em streaming seria um ADR futuro; hoje não há demanda.
