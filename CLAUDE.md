# ensaios-ni

Software de aquisição de dados para hardware **National Instruments** (chassi cDAQ-9184 + módulos 9205 e 9235), substituindo LabVIEW/FlexLogger (pagos) por um programa próprio em Python sobre o driver gratuito **NI-DAQmx**.

> Este `CLAUDE.md` **complementa** o global (`~/.claude/CLAUDE.md`) e o do cofre.
> Em conflito, vale o mais específico (este). Português em tudo continua valendo.
>
> **Todo o desenvolvimento acontece neste Mac.** Windows (do dev e do tio) é só
> configuração/execução e a **validação física** — coberta pelo guia humano
> [docs/guia-teste-hardware.md](docs/guia-teste-hardware.md), não por agente.

---

## Contexto antes de mexer

Leia **sempre** antes de implementar:

1. [docs/onde-pesquisar.md](docs/onde-pesquisar.md) — **protocolo de dúvida**: o usuário é o tio (OFM); siga o padrão do AqDados/área (compatibilidade > invenção). Onde buscar resposta antes de perguntar ou inventar.
2. [docs/contexto-hardware.md](docs/contexto-hardware.md) — inventário do hardware, restrições e a **API real do `nidaqmx` pinada** (não inventar assinaturas).
3. [CONTEXT.md](CONTEXT.md) — glossário do domínio (tensão, strain, task, porta, adaptador…).
4. [docs/adr/](docs/adr/) — decisões de arquitetura (**índice em [docs/adr/README.md](docs/adr/README.md)** — leia antes de abrir ADR por ADR). **ADR-001 define a espinha dorsal** (porta/adaptador).
5. [docs/roadmap.md](docs/roadmap.md) — plano em fases e **onde estamos** (fonte única do status). Ao **retomar**, leia também o handoff mais recente (ver [docs/handoff/](docs/handoff/)).
6. Brief no cofre: `~/cofre/01-projetos/ensaios-ni.md` — contexto do projeto e perguntas pendentes pro dono do hardware.

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
6. **`import PySide6` só na camada de widget** (`src/ensaios_ni/apresentacao/qt/`). Os Presenters (`apresentacao/monitor.py`, `apresentacao/afericao.py`) e o resto são Python puro, testáveis no Mac sem display — ver [ADR-015](docs/adr/015-ux-e-fluxo-do-dashboard.md). `PySide6`/`pyqtgraph` são extra opcional `[gui]`; teste-guarda de AST trava o resto.

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
- **Persistência:** CSV primeiro. TDMS/PostgreSQL só se a necessidade aparecer. Escrita de config (aferição) com `tomlkit` (preserva comentários; o `tomllib` é só leitura) — única dep core, ver [ADR-017](docs/adr/017-afericao-na-ui-e-escrita-de-config.md).
- **Dashboard:** PyQt6/PySide6 + pyqtgraph (Fase 4) — ver [ADR-013](docs/adr/013-stack-do-dashboard.md).
- **Dependências:** `pyproject.toml`. No Mac, `uv` (ARM-native) é o preferido; no Windows do tio, `pip install -e .` simples basta.

---

## Estrutura

`apresentacao/` (dashboard, Fase 4) tem as fatias 1–4 (monitor ao vivo, XY/multicanal, aferição na UI, metadata + exportar + tara) — Fase 4 concluída; ver [roadmap.md](docs/roadmap.md).

```text
ensaios-ni/
├── CLAUDE.md · CONTEXT.md · README.md · pyproject.toml
├── config/
│   └── canais.exemplo.toml        # mapeamento canal → conversão (regressão/segmento/linear)
├── docs/
│   ├── onde-pesquisar.md          # protocolo de dúvida + filosofia de produto
│   ├── contexto-hardware.md
│   ├── guia-teste-hardware.md     # validação no hardware real do tio (Fase 5)
│   └── adr/001…020                # decisões de arquitetura
├── src/ensaios_ni/
│   ├── dominio/                   # Canal, conversão, regressao (Reta), SerieTemporal, Metadata (testável no Mac)
│   ├── aquisicao/
│   │   ├── porta.py               # interface FonteDeAquisicao
│   │   ├── fake.py                # adaptador sintético (Mac)
│   │   └── daqmx.py               # adaptador real (Windows, nidaqmx lazy)
│   ├── persistencia/              # CSV + config_canais.py (TOML) + metadata_ensaio.py (.meta.toml) + exportadores/
│   ├── aplicacao/                 # casos de uso (ensaio finito/contínuo) + demo
│   ├── apresentacao/              # dashboard (Fase 4): monitor.py + afericao.py + exportacao.py (Presenters) + qt/ (widget PySide6)
│   └── __main__.py                # CLI (--fonte, --continuo, --exportar)
└── tests/
    ├── dominio/ · aquisicao/ · aplicacao/ · persistencia/ · arquitetura/
```

---

## Manutenção da documentação (gatilho → ação)

Regra-mãe ([ADR-014](docs/adr/014-fonte-unica-na-documentacao.md)): **informação volátil tem dono
único; os demais docs apontam, não copiam.** Ao concluir uma mudança, atualize **só o dono**:

| Quando você… | Atualize (o dono) |
| ------------ | ----------------- |
| Cria ou muda o status de um **ADR** | a linha no índice [docs/adr/README.md](docs/adr/README.md) + `CHANGELOG.md` + o range `adr/001…NNN` na Estrutura acima |
| Avança de fase ou muda o **status** do projeto | **só** o [roadmap.md](docs/roadmap.md) — nunca copie status em README/CLAUDE/contexto-hardware |
| **Encerra a sessão** | gere um handoff com `/handoff` em [docs/handoff/](docs/handoff/) (vira o ponto de entrada da próxima sessão) |
| Conclui uma **feature/correção** relevante | `CHANGELOG.md` (seção certa) |
| Define **vocabulário** novo de domínio | [CONTEXT.md](CONTEXT.md) |

**Os dois índices `README.md` têm naturezas diferentes:**

- [docs/adr/README.md](docs/adr/README.md) é **lista viva** — atualize a tabela a cada ADR novo ou com status alterado.
- [docs/handoff/README.md](docs/handoff/README.md) é **estável** (não cita o handoff "mais recente" por nome, de propósito) — só mexa se a *política* de handoff mudar, nunca a cada sessão.

Antes de colar um trecho em outro arquivo, pergunte: *quem é o dono dessa informação?* Se já tem
dono, **linke** em vez de copiar. Exceção única: a **armadilha do strain** é repetida de propósito
(segurança).

---

## Git (reforço do global)

- Branch de trabalho: `develop`. Nunca tocar `main` direto.
- **Nunca** commitar/push autônomo — só quando o Weslley pedir.
- Commits de aquisição/domínio (backend) separados de dashboard (frontend).
