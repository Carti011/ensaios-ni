# ensaios-ni

Software de aquisição de dados para hardware **National Instruments** (chassi cDAQ-9184 + 2× NI 9205 + 1× NI 9235), em Python, sobre o driver gratuito **NI-DAQmx**. Substitui LabVIEW/FlexLogger (pagos) por uma aplicação própria que lê os sensores, converte para unidade de engenharia e registra/exibe os ensaios.

> **Status: em planejamento.** Ainda sem código — só documentação e plano. Ver `CLAUDE.md`, `CONTEXT.md` e `docs/`.

## Pré-requisitos

- **Sistema:** Windows (ou Linux x86). **Não roda em macOS nem ARM** — o NI-DAQmx não existe nessas plataformas. O Mac serve só para desenvolver e rodar os testes de domínio.
- **Driver NI-DAQmx** (gratuito, [ni.com](https://www.ni.com)) instalado no Windows.
- **NI-MAX** (vem com o driver) para descobrir/nomear o chassi e validar canais.
- **Python 3.12+**.

## Como rodar

> A definir na Fase 0 (setup do ambiente). Será preenchido junto com o `pyproject.toml`.

## Variáveis de ambiente

> A definir. Nomes de dispositivo e mapeamento de canais vão para `config/canais.toml`, não para o código.

## Documentação

- [CLAUDE.md](CLAUDE.md) — regras do projeto para o agente.
- [CONTEXT.md](CONTEXT.md) — glossário do domínio.
- [docs/contexto-hardware.md](docs/contexto-hardware.md) — inventário do hardware e **API do `nidaqmx` pinada**.
- [docs/adr/](docs/adr/) — decisões de arquitetura.

## Licença

[MIT](LICENSE) — © 2026 Weslley Cardoso.

## Estrutura planejada

```text
ensaios-ni/
├── config/canais.toml          # mapeamento canal → conversão (vem do dono do hardware)
├── docs/                        # contexto de hardware + ADRs
├── src/ensaios_ni/
│   ├── dominio/                 # conversão volts→unidade (testável no Mac)
│   ├── aquisicao/               # porta + adaptadores (fake / daqmx)
│   ├── persistencia/            # CSV
│   └── apresentacao/            # dashboard (Fase 3)
└── tests/
```
