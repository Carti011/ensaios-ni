# ensaios-ni

Software de aquisição de dados para hardware **National Instruments** (chassi cDAQ-9184 + 2× NI 9205 + 1× NI 9235), em Python, sobre o driver gratuito **NI-DAQmx**. Substitui LabVIEW/FlexLogger (pagos) por uma aplicação própria que lê os sensores, converte para unidade de engenharia e registra/exibe os ensaios.

> **Status: Fase 1 (domínio).** Porta `FonteDeAquisicao`, adaptador `fake` e conversão volts→unidade já existem e são testáveis no Mac, sem hardware e sem `nidaqmx`. A aquisição real (`daqmx`) entra na Fase 2, no Windows. Ver `CLAUDE.md`, `CONTEXT.md` e `docs/`.

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

### Aquisição real (só Windows, Fase 2)

Com o driver NI-DAQmx instalado, instale o pacote com o extra de hardware:

```bash
pip install -e .[hardware]
```

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
