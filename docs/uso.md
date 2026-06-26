# Uso — ensaios-ni

Guia operacional: instalar, rodar um ensaio e exportar. Para a visão geral e a arquitetura, ver o
[README](../README.md).

## Pré-requisitos

- **Desenvolvimento (domínio + adaptador fake):** qualquer plataforma com **Python 3.12+**.
  Recomendado o [uv](https://docs.astral.sh/uv/) (ARM-native no Mac).
- **Aquisição real:** **Windows** (ou Linux x86). Não roda em macOS nem ARM — o NI-DAQmx não
  existe nessas plataformas.
- **Driver NI-DAQmx** (gratuito, [ni.com](https://www.ni.com)) instalado no Windows.
- **NI-MAX** (vem com o driver) para descobrir o chassi e validar canais.

## Rodar os testes (qualquer plataforma, sem hardware)

O domínio e o adaptador fake rodam em qualquer lugar, sem o `nidaqmx`:

```bash
uv run pytest
```

## Demonstração no Mac (sem hardware)

Roda um ensaio ponta a ponta com o adaptador fake e um sinal sintético, gerando um CSV de exemplo.
Mostra o fluxo ler → converter → gravar antes de existir o adaptador real:

```bash
PYTHONPATH=src uv run python -m ensaios_ni
```

No Mac o pacote não é instalado (`package = false`), por isso o `PYTHONPATH=src`. No Windows,
depois de `pip install -e .[hardware]`, basta `python -m ensaios_ni`.

## Aquisição real (Windows)

Instale com o extra de hardware e rode lendo os canais (hardware ou dispositivos simulados do
NI-MAX), com os parâmetros por linha de comando:

```bash
pip install -e .[hardware]
python -m ensaios_ni --fonte daqmx --config config/canais.toml --taxa 1024 --amostras 1024 --saida ensaio.csv
```

`--fonte fake` (padrão) roda a demonstração sintética em qualquer plataforma; `--fonte daqmx` exige
Windows + NI-DAQmx. Os nomes dos canais no `canais.toml` vêm do NI-MAX. O critério de "funcionou" é
a leitura bater com o test panel do NI-MAX no mesmo canal.

Para aquisição contínua de longa duração, use `--continuo` com `--duracao-s` e `--bloco`. Passo a
passo de instalação no Windows: [guia-windows.md](guia-windows.md). Runbook de validação:
[validacao-windows.md](validacao-windows.md).

## Exportar um ensaio

Um CSV gravado vira outro formato sem rodar nova aquisição (serve para reexportar ensaios antigos):

```bash
# CSV amigável ao Excel BR (separador ; e decimal vírgula), sem dependência extra
PYTHONPATH=src uv run python -m ensaios_ni --exportar csv-excel-br --de ensaio.csv --saida ensaio-br.csv

# .xlsx nativo (exige o extra [excel], openpyxl)
PYTHONPATH=src uv run python -m ensaios_ni --exportar xlsx --de ensaio.csv --saida ensaio.xlsx

# só alguns canais
PYTHONPATH=src uv run python -m ensaios_ni --exportar xlsx --de ensaio.csv --saida ensaio.xlsx --sinais "Mod1/ai0,Mod3/ai0"

# só um trecho (janela de tempo em segundos), útil para ensaios longos
PYTHONPATH=src uv run python -m ensaios_ni --exportar xlsx --de ensaio.csv --saida trecho.xlsx --inicio-s 120 --fim-s 180

# TXT para o AqDAnalysis (formato provisório, ver nota)
PYTHONPATH=src uv run python -m ensaios_ni --exportar txt-aqanalysis --de ensaio.csv --saida ensaio.txt
```

O `.xlsx` precisa do `openpyxl` (extra `[excel]`; no Mac o grupo `dev` já o inclui). O
`txt-aqanalysis` usa decimal vírgula e TAB, mas o layout do "Importa Arquivo Texto" do AqDAnalysis
ainda não foi validado contra um arquivo real (ver [ADR-011](adr/011-estrategia-de-exportacao.md)).

## Configuração

Não há segredos no código. O mapeamento canal → conversão fica em `config/canais.toml` — copie de
`config/canais.exemplo.toml` e preencha com os valores do hardware. O `canais.toml` real é ignorado
no git.
