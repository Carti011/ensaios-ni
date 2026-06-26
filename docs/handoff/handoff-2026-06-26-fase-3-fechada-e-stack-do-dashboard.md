# Handoff: Fase 3 (backend) fechada e stack do dashboard decidida (PyQt6/pyqtgraph)

**Data:** 2026-06-26
**Status:** aguardando decisão (próxima sessão = **design/UX do dashboard**, em outro chat). Backend completo, 105 testes verdes. PR develop→main a abrir nesta sessão.

## 1. Objetivo

Substituir o **FlexLogger** (única peça paga da pilha NI) por software próprio em Python sobre o **NI-DAQmx** (gratuito), para o tio do Weslley (OFM Engenharia: cDAQ-9184 + 2× NI 9205 de tensão + 1× NI 9235 de strain). **Critério de sucesso: o tio largar o FlexLogger e usar o nosso no trabalho real** (provas de carga e vibração em estruturas). Esta sessão **fechou o backend da Fase 3** (calibração por regressão + exportadores) e **decidiu a stack do dashboard** (Fase 4).

## 2. Contexto essencial

- **Stack:** Python 3.12, `pytest`, `uv` (Mac). `nidaqmx` é extra opcional `[hardware]` (só Windows/Linux x86 — **não roda em macOS/ARM**); `openpyxl` é extra opcional `[excel]`. ~90% testável no Mac.
- **Arquitetura porta/adaptador** (ADR-001): porta `FonteDeAquisicao`; `import nidaqmx` **só** em `aquisicao/daqmx.py` e **lazy**. Teste-guarda (AST) trava o resto. Há teste-guarda análogo para `openpyxl` (só lazy).
- **Norte de produto = Lynx (AqDados + AqDAnalysis)** (ADR-010), que o tio domina. FlexLogger/NI-DAQmx = referência **técnica** do driver. Protocolo de dúvida em `docs/onde-pesquisar.md` (produto→Lynx; técnica→NI; domínio→site OFM em `codigo/ofm-engenharia/` e ofmengenharia.com.br; Google é fonte legítima).
- **Filosofia de produto (decidida nesta sessão):** não copiar — **núcleo técnico segue o padrão de mercado**, **fluxo espelha o tio (AqDados)**, **entrega (UX/exportação) a gente melhora**. O usuário é o tio, não o Weslley.
- **Calibração = regressão linear** é o padrão do tio (AqDados; ele fabrica/calibra células de carga com rastreabilidade INMETRO/RBC). A interpolação por segmento veio do FlexLogger (norte antigo).
- **Estratégia de exportação (ADR-011):** software faz aquisição+calibração; análise fica no AqDAnalysis. Interop por TXT (não geramos `.LDT` proprietário); Excel porque o tio valoriza.

## 3. O que já foi feito (nesta sessão)

**Exportadores plugáveis (ADR-012, TDD):**
- Value object `SerieTemporal` (`dominio/serie.py`) — moeda comum entre ensaio e exportadores.
- `carregar_csv` (`persistencia/csv_ensaio.py`) — inverso de `gravar_ensaio` (reconstrói a série de um CSV; reexporta ensaios antigos).
- `persistencia/exportadores/`: **csv_excel_br** (`;` + decimal vírgula + BOM), **xlsx** (openpyxl lazy, números nativos), **txt_aqanalysis** (TAB + decimal vírgula — **PROVISÓRIO**, ver bloqueios). Helpers em `comum.py` (`selecionar`, `cabecalho`, `numero_virgula`, `iterar_amostras`, `resolver_janela`). Registro plugável `EXPORTADORES`.
- **Seleção de sinais** e **janela de tempo** (`inicio_s`/`fim_s`) em todos; janela inválida recusada cedo, sem criar arquivo.
- CLI: `--exportar {csv-excel-br,xlsx,txt-aqanalysis} --de ... --saida ... [--sinais a,b] [--inicio-s] [--fim-s]`. Erro de input vira mensagem limpa (sem traceback).

**Calibração por regressão (ADR-006 revisado, TDD):**
- `dominio/regressao.py`: `ajustar_regressao(pontos) -> Reta(a, b, correlacao)` (mínimos quadrados + Pearson). `converter` aplica a reta.
- Config: `pontos` usa **regressão por padrão**; `metodo = "segmento"` é opt-in (interpolação, para não-lineares). Regressão aceita volts repetido (medições); segmento mantém clamp/ordenação/unicidade. `canais.exemplo.toml` demonstra os dois.

**Documentação/planejamento:**
- `docs/onde-pesquisar.md` (protocolo de dúvida + filosofia de 3 camadas).
- `docs/roadmap.md` (plano do início ao fim).
- `docs/tarefas-futuras.md` (backlog: validar TXT, etc.).
- **ADR-013 (Aceito): stack do dashboard = PyQt6/PySide6 + pyqtgraph.**
- CLAUDE.md (estrutura atualizada + onde-pesquisar como 1ª leitura), CONTEXT, CHANGELOG, README atualizados.

**Git:** sincronizada a develop com a main (PR #4 já fora mergeada); ~13 commits novos na develop nesta sessão (exportadores, calibração, janela, txt, docs, decisão de stack).

## 4. Estado atual

- **105 testes verdes** no Mac (`uv run pytest`), sem `nidaqmx`. Teste-guarda de arquitetura (nidaqmx + openpyxl) verde.
- **Backend completo:** ler (tensão+strain, finito+contínuo) → calibrar (regressão/segmento/linear + tara) → gravar CSV → exportar (3 formatos, com sinais e janela). Tudo por **CLI**.
- **Fase 3 (backend) = FECHADA.** Working tree limpo. Falta a **interface gráfica** (Fase 4) — o que o tio realmente vai usar.

## 5. Bloqueios e dependências

- **PR develop→main:** a abrir nesta sessão; merge na main é só do Weslley.
- **TXT-AqAnalysis é provisório:** separador/encoding/cabeçalho a calibrar com um TXT autêntico do tio (já pedido a ele, aguardando) **ou** testar a importação no AqDAnalysis dele (Fase 5). Ver `docs/tarefas-futuras.md`. **Não bloqueia o dashboard.**
- **Número físico do strain:** só no hardware do tio (Fase 5).
- **Windows não é necessário agora:** Fase 3 inteira é testável no Mac (e está). O dashboard (Fase 4) também pode ser desenvolvido no Mac — **PySide6/pyqtgraph rodam em ARM** — com o adaptador **fake**. Windows só volta na Fase 5 (hardware real) e pra testar o TXT.

## 6. Próximos passos (Fase 4 — dashboard, em OUTRO chat)

1. **Começar pelo design/UX, não pela implementação.** Desenhar o fluxo de telas espelhando o **AqDados** (ver `docs/referencia-lynx.md`): tabela de canais, **aferição** (pontos + regressão + correlação + tara), controle de ensaio, e **visualização em tempo real**. Considerar a skill `/planejar-ux` ou `/criar-ui`.
2. **Telas mínimas (MVP):** (a) configurar/calibrar canais; (b) **ver o sinal ao vivo** (sinal×tempo, **XY carga×deformação**, FFT na vibração); (c) iniciar/parar/duração + metadata do ensaio (obra, data, sensor); (d) exportar (reusa os exportadores prontos).
3. **Implementar com PyQt6/PySide6 + pyqtgraph** consumindo a porta `FonteDeAquisicao` (fake no Mac, daqmx no Windows). Nova camada `src/ensaios_ni/apresentacao/` (ainda não existe).
4. **Manter o backend intacto:** a porta já entrega tudo; a UI só consome. Domínio segue testável no Mac.
5. Depois: Fase 5 (validação física no tio) e Fase 6 (empacotar em `.exe`, robustez, adoção).

## 7. Artefatos relevantes

- **Roadmap e decisões:** `docs/roadmap.md`, `docs/adr/013-stack-do-dashboard.md` (stack), `docs/adr/010` (norte Lynx), `docs/adr/011`/`012` (exportação), `docs/adr/006` (calibração), `docs/onde-pesquisar.md`, `docs/tarefas-futuras.md`, `docs/referencia-lynx.md` (UX do AqDados a espelhar).
- **Código backend:** `aquisicao/{porta,fake,daqmx}.py`, `dominio/{canais,conversao,regressao,serie}.py`, `persistencia/csv_ensaio.py` + `persistencia/exportadores/`, `aplicacao/ensaio.py`, `__main__.py`.
- **Comandos:**
  - `uv run pytest` → **105 passed**.
  - Demo: `PYTHONPATH=src uv run python -m ensaios_ni --amostras 8 --taxa 16 --saida /tmp/e.csv`
  - Exportar: `PYTHONPATH=src uv run python -m ensaios_ni --exportar xlsx --de /tmp/e.csv --saida /tmp/e.xlsx --inicio-s 0.1 --fim-s 0.3`
- **Interface da porta (o que o dashboard vai consumir):**
  ```python
  fonte.ler_tensao(canais, amostras, taxa_hz) -> dict[str, list[float]]
  fonte.ler_strain(canais, amostras, taxa_hz) -> dict[str, list[float]]
  fonte.transmitir_tensao(canais, taxa_hz, amostras_por_bloco) -> Iterator[dict[str, list[float]]]
  fonte.transmitir_strain(canais, taxa_hz, amostras_por_bloco) -> Iterator[dict[str, list[float]]]
  ```

## 8. Como iniciar a próxima sessão (design do front, no Mac)

1. Ler este handoff, `docs/roadmap.md`, `docs/adr/013-stack-do-dashboard.md` e `docs/referencia-lynx.md` (a UX do AqDados a espelhar).
2. `uv run pytest` → **105 passed** (confirma o backend de base).
3. Confirmar com o Weslley se a **PR foi mergeada** na main; se sim, sincronizar a develop.
4. **Não codar tela ainda:** rodar o discovery de UX (telas, fluxo, o que mostrar ao vivo), espelhando o AqDados. Só depois implementar PyQt6/pyqtgraph com o adaptador **fake** (roda no Mac).
5. Regras: import `nidaqmx` só no `daqmx.py` (lazy); strain nunca usa defaults da API; português em tudo; commits separados por camada (backend ≠ frontend); nada de commit/push/merge autônomo.
