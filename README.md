# ensaios-ni

Software de aquisição de dados para hardware **National Instruments** (chassi cDAQ-9184 + 2× NI 9205 + 1× NI 9235), em Python, sobre o driver gratuito **NI-DAQmx**. Substitui LabVIEW/FlexLogger (pagos) por uma aplicação própria que lê os sensores, converte para unidade de engenharia e registra/exibe os ensaios.

O programa é **config-driven**: o que muda de um ensaio para outro (quais canais, quais sensores, qual conversão) vive em arquivo de configuração, não no código. Medir um prédio, uma ponte ou uma peça é o **mesmo programa** lendo um `config/canais.toml` diferente.

> **Status: Fase 2 (aquisição de tensão).** Porta `FonteDeAquisicao` (multi-canal, com taxa), adaptador `fake`, conversão volts→unidade e persistência CSV são testáveis no Mac sem `nidaqmx`. O adaptador real `daqmx` **lê tensão (9205)** e roda no Windows. Strain (9235) entra numa fatia seguinte, com o gage factor do dono. Ver `CLAUDE.md`, `CONTEXT.md` e `docs/`.

## Pré-requisitos

- **Desenvolvimento (domínio + fake):** qualquer plataforma com **Python 3.12+**. Recomendado **[uv](https://docs.astral.sh/uv/)** (ARM-native no Mac).
- **Aquisição real:** **Windows** (ou Linux x86). **Não roda em macOS nem ARM** — o NI-DAQmx não existe nessas plataformas.
- **Driver NI-DAQmx** (gratuito, [ni.com](https://www.ni.com)) instalado no Windows.
- **NI-MAX** (vem com o driver) para descobrir/nomear o chassi e validar canais.

## Como rodar

### Testes do domínio (Mac/Linux/Windows, sem hardware)

O domínio e o adaptador fake rodam em qualquer plataforma, sem o `nidaqmx`. O `uv` cuida do Python 3.12 e das dependências de teste:

```bash
uv run pytest
```

### Ver o programa rodar (demonstração no Mac, sem hardware)

Roda um ensaio ponta a ponta com o adaptador **fake** e um sinal sintético, gerando um
CSV de exemplo (`ensaio-demo.csv`). Mostra o fluxo completo — ler → converter → gravar —
antes de existir o adaptador real:

```bash
PYTHONPATH=src uv run python -m ensaios_ni
```

> No Mac o pacote não é instalado (`package = false`), por isso o `PYTHONPATH=src`.
> No Windows, após `pip install -e .[hardware]`, basta `python -m ensaios_ni`.

### Aquisição real de tensão (só Windows)

Com o driver NI-DAQmx instalado, instale o pacote com o extra de hardware:

```bash
pip install -e .[hardware]
```

Rode um ensaio lendo os canais de tensão (hardware ou dispositivos simulados do NI-MAX),
escolhendo a fonte e os parâmetros por linha de comando:

```bash
python -m ensaios_ni --fonte daqmx --config config/canais.toml --taxa 1024 --amostras 1024 --saida ensaio.csv
```

> `--fonte fake` (padrão) roda a demonstração sintética em qualquer plataforma; `--fonte daqmx`
> exige Windows + NI-DAQmx. Os nomes dos canais no `canais.toml` vêm do NI-MAX.
> **Critério de "funcionou": a leitura bate com o test panel do NI-MAX** no mesmo canal.

**Passo a passo simples para o Windows** (instalação, driver NI, configuração de
canais — com ou sem Claude Code): [docs/guia-windows.md](docs/guia-windows.md).

## Variáveis de ambiente

Não há segredos no código. O mapeamento de canais (nomes de dispositivo e coeficientes de conversão) vai para `config/canais.toml` — copie de `config/canais.exemplo.toml`. O `canais.toml` real é ignorado no git.

## Documentação

- [CLAUDE.md](CLAUDE.md) — regras do projeto para o agente.
- [CONTEXT.md](CONTEXT.md) — glossário do domínio.
- [docs/contexto-hardware.md](docs/contexto-hardware.md) — inventário do hardware e **API do `nidaqmx` pinada**.
- [docs/adr/](docs/adr/) — decisões de arquitetura.

## Licença

[MIT](LICENSE) — © 2026 Weslley Cardoso.

## Estrutura

```text
ensaios-ni/
├── config/
│   └── canais.exemplo.toml      # modelo do mapeamento canal → conversão
├── docs/                        # contexto de hardware + ADRs
├── src/ensaios_ni/
│   ├── dominio/                 # Canal, conversão volts→unidade, erros (testável no Mac)
│   ├── aquisicao/               # porta + adaptadores (fake / daqmx)
│   ├── persistencia/            # CSV (Fase 2)
│   └── apresentacao/            # dashboard (Fase 3)
└── tests/                       # dominio / aquisicao / arquitetura
```
