# Handoff: Fase 1 — porta, fake e conversão (vertical slice no Mac)

**Data:** 2026-06-20
**Status:** em andamento — Fase 1 concluída e commitada; Fase 2 pendente (exige Windows)

## 1. Objetivo

Substituir LabVIEW/FlexLogger (pagos) por software próprio em Python sobre o driver gratuito NI-DAQmx, para o hardware do tio (chassi cDAQ-9184 + 2× NI 9205 de tensão + 1× NI 9235 de strain). Esta sessão montou a **Fase 1**: uma vertical slice fina que roda **100% no Mac M4, sem hardware e sem `nidaqmx`** — porta de aquisição, adaptador fake e domínio de conversão volts→unidade de engenharia, tudo via TDD.

## 2. Contexto essencial

- **Stack:** Python 3.12 (gerenciado por `uv`), `pytest`. `nidaqmx` é extra opcional `[hardware]` no `pyproject.toml`, **não instalado no Mac**.
- **Restrição que define tudo:** NI-DAQmx só roda em Windows/Linux x86. O Mac só desenvolve e testa domínio/fake. O pacote precisa importar e os testes do domínio precisam rodar sem `nidaqmx`.
- **Arquitetura porta/adaptador (ADR-001):** todo o sistema depende só da interface `FonteDeAquisicao`. Dois adaptadores: `daqmx` (real, Windows, único que importa `nidaqmx`, lazy) e `fake` (sintético, Mac).
- **Regras inegociáveis:** (1) `import nidaqmx` só em `daqmx.py`, lazy; (2) tudo depende da porta; (3) conversão vive em config, nunca hardcode; (4) strain (9235) nunca usa defaults da API (sempre `QUARTER_BRIDGE_I`, 120 Ω, 2,0 V).
- **ADR-002 (criado nesta sessão):** a porta retorna **volts brutos** (`list[float]`, sem timestamp); conversão é **linear por canal** (`ganho·V + offset`); config é validada no carregamento.
- **Ambiente decidido:** `uv` 0.11.23 via Homebrew + Python 3.12.13 (uv baixa e gerencia); `.venv` ignorado; `uv.lock` versionado.

## 3. O que já foi feito

Cronológico:

- Lido todo o contexto (CLAUDE.md, CONTEXT.md, contexto-hardware.md, ADR-001).
- Setup: `uv` via brew; `pyproject.toml` (src-layout, extra `[hardware]`, `[tool.uv] package=false`, pytest `pythonpath=["src"]`); venv 3.12.
- **Tracer bullet (TDD RED→GREEN):** fake devolve 2,0 V em `Mod1/ai0` → config linear (ganho 100) → `converter` → 200,0 kgf.
- **Lote 1 — fake barulhento:** canal inexistente, amostras demais e `amostras ≤ 0` agora falham com `ValueError` claro (antes o `[:amostras]` mentia em silêncio).
- **Lote 2 — erros de domínio:** `CanalNaoConfigurado` (canal fora da config) e `ConfiguracaoInvalida` (campo faltando ou não-numérico, apontando canal+campo). Config externa passou a ser validada.
- **Lote 3 — teste-guarda de arquitetura:** varre `src/` via **AST** e falha se `nidaqmx` for importado fora de `daqmx.py`. AST evita o falso-positivo que o `grep` dava na docstring de `porta.py`.
- **Lote 4 — regressões:** offset≠0 e múltiplas amostras (passaram de imediato; a fórmula já estava completa).
- **Lote 5 — docs:** `config/canais.exemplo.toml`, ADR-002, README (status Fase 1 + como rodar), CHANGELOG.
- **5 commits separados** na branch `develop` (chore / feat aquisicao / feat dominio / test arquitetura / docs).

Adiado **de propósito** (registrado no ADR-002):

- Conversão não-linear (termopar, strain) — não sabemos os sensores ainda; vira ADR-003 quando o dono confirmar.
- Value object `Medida(valor, unidade)` — YAGNI até persistência/dashboard precisar.
- Validar `tipo` do canal na leitura — `tipo` só ganha uso na Fase 2 (escolher a task DAQmx).
- `daqmx.py` real — exige Windows; fora do escopo da sessão.

## 4. Estado atual

- **15 testes verdes** (`uv run pytest`), rodando no Mac sem `nidaqmx`.
- Estrutura existente:
  - `src/ensaios_ni/dominio/` → `canais.py` (`Canal`, `Canais`, `carregar_canais`), `conversao.py` (`converter`), `erros.py`.
  - `src/ensaios_ni/aquisicao/` → `porta.py` (`FonteDeAquisicao`), `fake.py` (`AquisicaoFake`).
  - Ainda **não** existem: `aquisicao/daqmx.py`, `persistencia/`, `apresentacao/`.
- Branch `develop`, working tree limpo, tudo commitado. **Nenhum push feito.**

## 5. Bloqueios e dependências

- **Gargalo real (não é código):** falta levantar com o dono do hardware os itens da §6 de `docs/contexto-hardware.md` — que transdutor em cada canal, **fórmula de conversão volts→unidade por canal** (o item mais importante), gage factor do extensômetro, confirmação quarter-bridge 120 Ω, lead wire resistance, taxa de amostragem e duração do ensaio, o que é um "resultado", e como o cDAQ conecta na rede. Sem isso, os coeficientes de conversão e o strain real não avançam.
- **Fase 2 exige Windows** com NI-DAQmx + dispositivos simulados no NI-MAX (não roda no Mac).

## 6. Próximos passos

1. **(Não-código)** Levantar com o dono os itens da §6 do contexto-hardware. Desbloqueia conversões reais e strain.
2. **(Mac, sem bloqueio)** Persistência CSV via TDD: gravar amostras convertidas (canal, valor, unidade) em CSV. Camada `persistencia/`. Não depende de hardware.
3. **(Mac)** Se a persistência pedir, introduzir `converter_amostras(volts, canal)` e/ou value object `Medida`.
4. **(Windows, Fase 2)** Implementar `aquisicao/daqmx.py`: `import nidaqmx` lazy; task de tensão (2× 9205, `add_ai_voltage_chan`); task de strain (9235 com `QUARTER_BRIDGE_I`, 120 Ω, 2,0 V — nunca os defaults). Validar contra o test panel do NI-MAX (critério objetivo de "funcionou").
5. **(Windows)** Aquisição contínua (`register_every_n_samples_acquired_into_buffer_event` ou `stream_readers.AnalogMultiChannelReader`).
6. **(Quando sensores confirmados)** ADR-003 para conversão não-linear (estratégia por `tipo`/`conversao`).
7. **(Windows do dono)** Copiar `config/canais.exemplo.toml` → `config/canais.toml` e preencher com nomes reais (do NI-MAX) e coeficientes reais.

## 7. Artefatos relevantes

**Comando único da suíte:**

```bash
uv run pytest
```

**Porta (contrato que todo o sistema conhece)** — `src/ensaios_ni/aquisicao/porta.py`:

```python
class FonteDeAquisicao(ABC):
    @abstractmethod
    def ler_tensao(self, canal: str, amostras: int) -> list[float]:
        """Lê `amostras` de tensão (volts brutos) do canal físico informado."""
        ...
```

**Conversão (domínio puro)** — `src/ensaios_ni/dominio/conversao.py`:

```python
def converter(volts: float, canal: Canal) -> float:
    return canal.ganho * volts + canal.offset
```

**Formato da config** — `config/canais.exemplo.toml`:

```toml
[canais."Mod1/ai0"]
tipo = "tensao"
unidade = "kgf"
ganho = 100.0
offset = 0.0
```

**Decisões:** `docs/adr/001-arquitetura-porta-adaptador.md`, `docs/adr/002-conversao-linear-e-contrato-da-porta.md`.

## 8. Como iniciar a próxima sessão

1. Abrir este handoff e o `CLAUDE.md` do projeto.
2. Rodar `uv run pytest` — deve dar **15 passed**. Se não der, o ambiente quebrou; recriar com `uv venv --python 3.12`.
3. Decidir o foco:
   - Se há respostas do dono do hardware → atualizar `config/canais.exemplo.toml` e considerar ADR-003 (não-linear).
   - Se não → seguir com **persistência CSV** (roda no Mac, sem bloqueio): começar pelo teste em `tests/persistencia/`, usando `/tdd`.
4. Manter a regra nº1 viva: o teste-guarda `tests/arquitetura/test_regra_nidaqmx.py` deve continuar verde a cada commit.
