# ADR 004 — Camada de aplicação (caso de uso de ensaio) e ponto de entrada

## Status

Aceito

## Contexto

Depois do [ADR-001](001-arquitetura-porta-adaptador.md) (porta/adaptador),
[ADR-002](002-conversao-linear-e-contrato-da-porta.md) (conversão) e
[ADR-003](003-persistencia-csv-do-ensaio.md) (persistência), existiam três peças isoladas
— aquisição (porta), domínio (conversão) e persistência (CSV) — mas **nada que as
costurasse num fluxo de ensaio**, nem um ponto de entrada para rodar o programa.

Restrição de sempre: o fluxo tem que rodar **no Mac, sem `nidaqmx`** (com o adaptador
fake) e, na Fase 2 no Windows, trocar **só o adaptador** pelo `daqmx` real.

## Decisão

- **Nova camada `aplicacao/`** (o "service" no vocabulário em camadas). Contém o caso de
  uso `executar_ensaio(fonte, canais, amostras, taxa_hz, caminho)`: lê cada canal da
  `fonte` (porta), converte com o domínio e grava via persistência. É a **única** camada
  que conhece as três pontas; domínio e persistência continuam sem se conhecer.
- **Ponto de entrada `python -m ensaios_ni`** (`__main__.py`), que chama
  `aplicacao/demo.py`: roda um ensaio ponta a ponta com o adaptador **fake** e um sinal
  sintético senoidal, gerando um CSV de demonstração. Prova o fluxo inteiro no Mac, sem
  hardware.
- **Execução:** no Mac o pacote não é instalado (`package = false` no `uv`), então roda
  com `PYTHONPATH=src python -m ensaios_ni`. No Windows, após `pip install -e .[hardware]`,
  roda direto com `python -m ensaios_ni`.

## Consequências

**Melhora:**

- Fluxo de ensaio completo e testável no Mac (caso de uso + demonstração executável).
- A Fase 2 vira essencialmente **trocar o `fake` pelo `daqmx`** dentro da mesma costura —
  o caso de uso não muda.

**Piora / pendente:**

- A demonstração é **fixa** (fake + senoide hardcoded). O **ponto de entrada de produção**
  — carregar `config/canais.toml`, escolher o adaptador real, receber taxa/duração por
  linha de comando — ainda não existe; entra com o `daqmx` na Fase 2.
- A **escolha do adaptador** (fake vs daqmx) ainda não é parametrizada; hoje a demo amarra
  o fake. Quando o `daqmx` existir, decidir como selecionar (flag, env, config).
