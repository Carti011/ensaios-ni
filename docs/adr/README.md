# Índice de ADRs — ensaios-ni

Decisões de arquitetura registradas. **Leia este índice antes de abrir os ADRs um a um** — ele
existe para você ir direto ao arquivo certo, sem varrer os 14. Para o estado/plano do projeto, ver
[roadmap.md](../roadmap.md); para o glossário, [CONTEXT.md](../../CONTEXT.md); para onde pesquisar
cada tipo de dúvida, [onde-pesquisar.md](../onde-pesquisar.md).

Convenção: `NNN-titulo.md`, numeração sequencial. Status segue o template do projeto
(`Proposto | Aceito | Substituído por ADR-XXX`). A **espinha dorsal é o
[ADR-001](001-arquitetura-porta-adaptador.md)** (porta/adaptador) — leia esse primeiro.

| ADR | Título | Status | O que decide (resumo) |
| --- | ------ | ------ | --------------------- |
| [001](001-arquitetura-porta-adaptador.md) | Arquitetura porta/adaptador | Aceito | Isola o `nidaqmx` atrás da porta `FonteDeAquisicao`; só `daqmx.py` o importa (lazy). Base de tudo. |
| [002](002-conversao-linear-e-contrato-da-porta.md) | Conversão linear e contrato da porta | Aceito · estendido por 005/006 | A porta devolve **volts brutos**; conversão linear (`ganho·V+offset`) vive no domínio, por config. |
| [003](003-persistencia-csv-do-ensaio.md) | Persistência em CSV | Aceito | CSV "wide": `tempo_s` (derivado da taxa) + 1 coluna/canal; grava valor convertido, unidade no cabeçalho. |
| [004](004-camada-de-aplicacao-e-ponto-de-entrada.md) | Camada de aplicação e ponto de entrada | Aceito | Caso de uso `executar_ensaio` costura porta→domínio→persistência; `python -m ensaios_ni`. |
| [005](005-contrato-multicanal-da-porta.md) | Contrato multi-canal + DAQmx de tensão | Aceito · validado Windows (22/06) | Porta lê por task, **multi-canal com taxa**; adaptador real de tensão (9205) com sample clock. |
| [006](006-calibracao-por-pontos.md) | Calibração por pontos e tara | Aceito · revisado (25/06) | Calibração por **regressão linear** (padrão) / segmento (opt-in) / linear; **tara** estilo "Zero Channel". |
| [007](007-aquisicao-continua.md) | Aquisição contínua | Aceito · validado Windows (25/06) | Streaming por blocos (`transmitir_*`), gravação CSV incremental para ensaios longos. |
| [008](008-paridade-funcional-flexlogger.md) | Paridade com o FlexLogger | **Parcialmente substituído por 010** | Vale só no nível **técnico do driver** (Custom Scales, clamp, sample clock). Produto migrou pro Lynx. |
| [009](009-leitura-de-strain-9235.md) | Leitura de strain do 9235 | Aceito · validado Windows (25/06) | Task separada; `ConfigStrain` com os parâmetros do 9235 (quarter 120 Ω / 2,0 V), **nunca os defaults da API**. |
| [010](010-paridade-com-o-lynx.md) | Paridade com o Lynx | Aceito (revisa 008) | Espelho de **produto/UX/vocabulário** = AqDados/AqDAnalysis (Lynx), que o tio domina. |
| [011](011-estrategia-de-exportacao.md) | Estratégia de exportação (TXT) | Aceito | Não reescrever a análise; **exportar** TXT (AqDAnalysis) e Excel; nunca gerar `.LDT` proprietário. |
| [012](012-serie-temporal-e-exportadores.md) | Série temporal + exportadores | Aceito | `SerieTemporal` + `carregar_csv`; exportadores plugáveis com seleção de sinais e janela de tempo. |
| [013](013-stack-do-dashboard.md) | Stack do dashboard (Fase 4) | Aceito | **PyQt6/PySide6 + pyqtgraph** (desktop nativo, `.exe`, tempo real). |
| [014](014-fonte-unica-na-documentacao.md) | Fonte única na documentação | Aceito | Cada info volátil tem **dono único**; os demais docs apontam, não copiam. |

## Fios condutores (para entender o porquê sem ler tudo)

- **Isolamento do hardware:** 001 → 005 → 007 → 009 (porta → tensão → contínuo → strain).
- **Conversão/calibração:** 002 → 006 (o linear vira caso particular da calibração por pontos/regressão).
- **Norte de produto:** 008 → 010 (FlexLogger caiu para referência técnica; o Lynx virou o espelho).
- **Exportação:** 011 → 012 (estratégia de interoperar via TXT → implementação plugável).

> Mantenha este índice atualizado ao criar um ADR novo (é o "dono" da lista de ADRs — [ADR-014](014-fonte-unica-na-documentacao.md)).
