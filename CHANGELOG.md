# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

## [Não lançado]

### Adicionado

- Estrutura do pacote Python (`pyproject.toml`, Python 3.12, `pytest`); `nidaqmx` como extra opcional `[hardware]`, não instalado no Mac.
- Porta `FonteDeAquisicao` (interface) com `ler_tensao`.
- Adaptador `fake` (dados sintéticos, Python puro) com leitura validada (canal inexistente, amostras demais e amostras não positivas falham claro).
- Domínio de conversão linear volts→unidade de engenharia (`ganho * volts + offset`), parametrizado por `config/canais.toml`.
- Carregamento e validação de `config/canais.toml` com erros de domínio (`CanalNaoConfigurado`, `ConfiguracaoInvalida`).
- Teste-guarda de arquitetura: falha se algum arquivo fora de `daqmx.py` importar `nidaqmx` (via AST).
- `config/canais.exemplo.toml` documentando o formato de configuração.
- ADR-002 — conversão linear por canal e contrato da porta retornando volts brutos.
- Persistência de ensaio em CSV (`persistencia/csv_ensaio.py`): grava série temporal com coluna de tempo derivada da taxa de amostragem e uma coluna por canal; unidade de engenharia no cabeçalho (`Mod1/ai0 (kgf)`); recusa canais com contagens diferentes de amostras e `taxa_hz` não positiva.
- Camada de aplicação (`aplicacao/ensaio.py`): caso de uso `executar_ensaio` que orquestra leitura (porta) → conversão (domínio) → gravação (persistência), sem acoplar as camadas.
- Ponto de entrada `python -m ensaios_ni` (`__main__.py` + `aplicacao/demo.py`): roda um ensaio ponta a ponta no Mac com o adaptador fake e sinal sintético senoidal, gerando CSV de demonstração.
- ADR-003 — persistência do ensaio em CSV (série temporal, layout wide, valores convertidos com unidade no cabeçalho).
- ADR-004 — camada de aplicação (caso de uso `executar_ensaio`) e ponto de entrada de demonstração.
- Guia de instalação no Windows para humano (`docs/guia-windows.md`), com trilha para quem tem Claude Code e para quem não tem.
- Seções no `CLAUDE.md`: regras essenciais auto-suficientes (válidas sem o CLAUDE.md global) e runbook de onboarding no Windows.
- Adaptador real `aquisicao/daqmx.py` para leitura de tensão (9205): monta a task, configura sample clock explícito e normaliza o retorno em `dict[canal -> list]`; import `nidaqmx` lazy, testado no Mac via mock (`sys.modules`).
- Ponto de entrada de produção: `python -m ensaios_ni` agora aceita `--fonte {fake,daqmx}`, `--config`, `--taxa`, `--amostras` e `--saida` (argparse), permitindo rodar a leitura real no Windows sem editar código.
- ADR-005 — contrato multi-canal da porta, adaptador DAQmx de tensão, aquisição finita e estratégia de teste por mock.
- Calibração por pontos no domínio (`pontos = [[volts, valor], ...]` por canal): interpolação linear por segmento e **clamp** fora da faixa, espelhando a *Table scale* do NI-DAQmx. O `ganho/offset` linear segue valendo como fallback (caso de 2 pontos).
- Tara (zero) por canal no domínio: `calcular_tara` tira a média do repouso na unidade de engenharia e `converter(..., tara=)` a subtrai — à la "Zero Channel" do FlexLogger; em repouso a leitura tarada é zero mesmo com escala deslocada.
- ADR-006 (Aceito) — calibração por pontos e tara, com as 3 decisões de design fundamentadas no comportamento do FlexLogger/DAQmx.
- ADR-008 — paridade funcional com o FlexLogger (norte de design); `docs/referencia-flexlogger.md` com a pesquisa e fontes.
- `config/canais.exemplo.toml` ganhou um canal calibrado por pontos (LVDT fictício) e documentação das duas formas de conversão.
- Tara no fluxo de ensaio: `executar_ensaio(..., amostras_tara=)` faz uma leitura de repouso antes da aquisição, calcula a tara por canal e a aplica na conversão; exposto na CLI via `--amostras-tara` (0 = sem tara, comportamento atual).
- Leitura de strain do 9235: porta `FonteDeAquisicao.ler_strain` (task separada, devolve strain adimensional) implementada no `fake` e no `daqmx`. `ConfigStrain` fixa os parâmetros corretos do 9235 (quarter-bridge, 120 Ω, excitação interna 2,0 V, gage factor 2,15 configurável, lead wire para 3 fios) — **nunca os defaults perigosos da API** (full-bridge 350 Ω / 2,5 V). Teste-guarda trava essa armadilha. microstrain é um canal linear com ganho 1.000.000 (sem código de domínio novo).
- `docs/referencia-lynx.md` — análise das telas do AqDados/AqDAnalysis que o dono enviou (vocabulário, modos de aferição/calibração, suíte de análise, formato `.LDT`/TXT, unidades e nomes de canais reais). Nova fonte de verdade de paridade de UX.
- ADR-010 — paridade com o Lynx (AqDados + AqDAnalysis) como referência primária de produto; revisa o ADR-008.
- ADR-011 — estratégia de exportação e interoperabilidade com o AqDAnalysis via TXT (camada de exportadores plugáveis; não reescrever a suíte de análise da Lynx). Inclui **Excel** como destino de saída (CSV amigável ao Excel BR — separador `;`, decimal vírgula — e/ou `.xlsx` nativo via `openpyxl`), por ser formato que o dono valoriza, e exportação **seletiva** de sinais.

- Integração de **tensão + strain no mesmo ensaio** (`aplicacao/ensaio.py`): o `executar_ensaio` particiona os canais pelo campo `tipo` (`tensao`/`strain`), lê cada grupo na sua task (`ler_tensao` do 9205, `ler_strain` do 9235) via o helper `_ler_por_tipo`, e grava tudo num CSV na ordem do config. A tara (`amostras_tara`) passa a valer para os dois tipos. A CLI lê strain automaticamente quando o `canais.toml` declara canais `tipo = "strain"` — sem mudança de assinatura.
- Validação do campo `tipo` no domínio (`dominio/canais.py`): aceita só `tensao` ou `strain`; tipo desconhecido levanta `ConfiguracaoInvalida` (protege contra typo silencioso).
- A demonstração no Mac (`python -m ensaios_ni`) passa a exibir **microstrain** junto da tensão: `canais.exemplo.toml` ativa um canal de strain (`Mod3/ai0`, `µε`, ganho 1e6) e a demo gera sinal sintético por tipo (tensão 0–10 V; strain ±1e-3 → ±1000 µε).

### Alterado

- **Norte de paridade alterado** (a partir dos prints do dono, 23/06): o espelho de produto passou do **FlexLogger** para o **Lynx (AqDados + AqDAnalysis)**, que o dono domina. ADR-008 marcado como **parcialmente substituído** pelo ADR-010 (segue valendo só no nível técnico do driver NI-DAQmx). CONTEXT.md atualizado com o vocabulário do Lynx (Aferição, Balanço, Repouso, Shunt Cal, Consulta, `.LDT`, Exportador) e unidades reais (µm/m, mm/s²).
- ADR-006 ganhou pendência registrada: o AqDados calibra por **regressão linear** (com correlação) e por **ganho e ponto de referência**, além da interpolação por segmento que adotamos — a refinar na fase de calibração.

- Contrato da porta `FonteDeAquisicao.ler_tensao` passou a ser **multi-canal com taxa**: `ler_tensao(canais, amostras, taxa_hz) -> dict[str, list[float]]`. Lê todos os canais numa única task sob o mesmo sample clock, mantendo-os alinhados no tempo (necessário para carga × deformação e FFT). O fake e o caso de uso `executar_ensaio` foram adaptados.
