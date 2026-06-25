# ensaios-ni

Software de aquisição de dados para hardware **National Instruments** (chassi cDAQ-9184 + módulos 9205 e 9235), substituindo LabVIEW/FlexLogger (pagos) por um programa próprio em Python sobre o driver gratuito **NI-DAQmx**.

> Este `CLAUDE.md` **complementa** o global (`~/.claude/CLAUDE.md`) e o do cofre.
> Em conflito, vale o mais específico (este). Português em tudo continua valendo.
>
> **Todo o desenvolvimento acontece neste Mac.** Windows (do dev e do tio) é só
> configuração/execução inicial — coberta pelo guia humano [docs/guia-windows.md](docs/guia-windows.md),
> não por agente.

---

## Contexto antes de mexer

Leia **sempre** antes de implementar:

1. [docs/onde-pesquisar.md](docs/onde-pesquisar.md) — **protocolo de dúvida**: o usuário é o tio (OFM); siga o padrão do AqDados/área (compatibilidade > invenção). Onde buscar resposta antes de perguntar ou inventar.
2. [docs/contexto-hardware.md](docs/contexto-hardware.md) — inventário do hardware, restrições e a **API real do `nidaqmx` pinada** (não inventar assinaturas).
3. [CONTEXT.md](CONTEXT.md) — glossário do domínio (tensão, strain, task, porta, adaptador…).
4. [docs/adr/](docs/adr/) — decisões de arquitetura. **ADR-001 define a espinha dorsal** (porta/adaptador).
5. Brief no cofre: `~/cofre/01-projetos/ensaios-ni.md` — estado atual, plano em fases, perguntas pendentes pro dono do hardware.

---

## Restrição que define toda a arquitetura

**NI-DAQmx só roda em Windows e Linux x86. Não existe em macOS nem ARM.**

Três ambientes, papéis distintos:

| Ambiente | Papel | Roda o quê |
| -------- | ----- | ---------- |
| **MacBook M4 (dev)** | escrever código, versionar, testar o domínio | testes de domínio + adaptador **fake** (`pytest`). **Nunca** o adaptador real. |
| **Windows do dev** | validar o adaptador real sem o hardware | dispositivos **simulados** no NI-MAX |
| **Windows do tio** | validação física e calibração | hardware real |

Consequência prática: **o pacote tem que importar e os testes do domínio têm que rodar no Mac sem o `nidaqmx` instalado.**

---

## Regras de arquitetura (inegociáveis)

1. **`import nidaqmx` só dentro do adaptador real** (`src/ensaios_ni/aquisicao/daqmx.py`), e **lazy** (dentro das funções, não no topo do módulo). Qualquer outro arquivo que importe `nidaqmx` é bug.
2. **Tudo depende da porta, nunca do adaptador.** Domínio, conversão, persistência e apresentação conhecem só a interface `FonteDeAquisicao` — ver [ADR-001](docs/adr/001-arquitetura-porta-adaptador.md).
3. **`nidaqmx` é dependência opcional** (extra `[hardware]` no `pyproject`). Dev no Mac instala sem ela.
4. **Conversão volts→unidade de engenharia vive em config** (`config/canais.toml`), **nunca hardcode**. Os valores vêm do dono do hardware.
5. **Strain (9235) nunca usa os defaults da API.** Sempre `QUARTER_BRIDGE_I`, 120 Ω, 2,0 V. Os defaults do `nidaqmx` são full-bridge 350 Ω / 2,5 V e produzem **número plausível e errado, sem lançar erro**. Ver contexto-hardware §4.

---

## TDD aqui

- **Domínio e fake → red-green-refactor no Mac.** É onde mora ~90% da lógica testável (conversão, persistência, regras de ensaio).
- **Adaptador DAQmx real → validação de integração no Windows**, comparando contra o **test panel do NI-MAX** no mesmo canal. Esse é o critério objetivo de "funcionou". Dispositivo simulado do NI-MAX **não** é teste unitário.
- Nenhuma feature entra sem teste correspondente.

---

## Stack

- **Python 3.12** (o `nidaqmx` exige 3.9+; restrição do dono do hardware: só Python).
- **Driver:** NI-DAQmx (gratuito, ni.com) — instalado no Windows, fora do repo.
- **Pacote:** `nidaqmx` (PyPI) — wrapper oficial do driver.
- **Testes:** `pytest`.
- **Persistência:** CSV primeiro. TDMS/PostgreSQL só se a necessidade aparecer.
- **Dashboard:** decisão adiada pra Fase 3 (vira ADR). Não fixar agora.
- **Dependências:** `pyproject.toml`. No Mac, `uv` (ARM-native) é o preferido; no Windows do tio, `pip install -e .` simples basta.

---

## Estrutura

`apresentacao/` (dashboard, Fase 3) ainda não existe — o resto está criado.

```text
ensaios-ni/
├── CLAUDE.md · CONTEXT.md · README.md · pyproject.toml
├── config/
│   └── canais.exemplo.toml        # mapeamento canal → conversão (regressão/segmento/linear)
├── docs/
│   ├── onde-pesquisar.md          # protocolo de dúvida + filosofia de produto
│   ├── contexto-hardware.md
│   └── adr/001…012                # decisões de arquitetura
├── src/ensaios_ni/
│   ├── dominio/                   # Canal, conversão, regressao (Reta), SerieTemporal (testável no Mac)
│   ├── aquisicao/
│   │   ├── porta.py               # interface FonteDeAquisicao
│   │   ├── fake.py                # adaptador sintético (Mac)
│   │   └── daqmx.py               # adaptador real (Windows, nidaqmx lazy)
│   ├── persistencia/              # CSV (gravar/carregar) + exportadores/ (csv-excel-br, xlsx)
│   ├── aplicacao/                 # casos de uso (ensaio finito/contínuo) + demo
│   └── __main__.py                # CLI (--fonte, --continuo, --exportar)
└── tests/
    ├── dominio/ · aquisicao/ · aplicacao/ · persistencia/ · arquitetura/
```

---

## Git (reforço do global)

- Branch de trabalho: `develop`. Nunca tocar `main` direto.
- **Nunca** commitar/push autônomo — só quando o Weslley pedir.
- Commits de aquisição/domínio (backend) separados de dashboard (frontend).
