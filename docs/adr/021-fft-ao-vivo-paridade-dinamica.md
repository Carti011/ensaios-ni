# ADR 021 — FFT ao vivo no dashboard (paridade dinâmica)

## Status

Aceito (01/07/2026). **Resolve o "ADR-árbitro" pendente** citado em
[ADR-011](011-estrategia-de-exportacao.md), [ADR-015](015-ux-e-fluxo-do-dashboard.md),
[ADR-019](019-foco-em-validacao-fisica-e-adocao.md) e em
[tarefas-futuras.md](../tarefas-futuras.md) (FFT ao vivo vs. exportar para o AqDAnalysis).
Decisão de **escopo/direção**; a implementação fica para uma fase própria (ver
[roadmap.md](../roadmap.md)).

## Contexto

O critério de sucesso do projeto é **o tio largar o FlexLogger** ([roadmap.md](../roadmap.md)).
Metade do trabalho dele é **vibração**: acelerômetro (Dytran 7523A1) a 1024 Hz para extrair
frequências naturais via **FFT** — ver [respostas-tio.md](../respostas-tio.md) e
[CONTEXT.md](../../CONTEXT.md).

O [ADR-011](011-estrategia-de-exportacao.md) decidiu **não reescrever a análise**: exportar TXT e
deixar FFT/fadiga/relatórios no AqDAnalysis. Isso é acertado para a **análise pesada**, mas tem uma
consequência que ficou pendente de arbitragem: no ensaio **dinâmico**, o tio **não vê a frequência
ao vivo** no nosso software — depende de exportar e abrir o AqDAnalysis. O FlexLogger tem
**Frequency Graph (FFT) ao vivo** ([referencia-lynx.md §3](../referencia-lynx.md)). Ou seja, com a
estratégia atual ele **larga o FlexLogger só no estático**; no dinâmico, não.

A decisão do dono do projeto (01/07/2026) é **substituir o FlexLogger por inteiro**, dinâmico
incluído.

## Decisão

**Implementar FFT ao vivo no dashboard** — o espectro de frequência atualizando durante a aquisição
de vibração, espelhando o Frequency Graph do FlexLogger.

Fronteira de escopo (não revoga o [ADR-011](011-estrategia-de-exportacao.md)):

- **Passa a ser nosso:** a **visualização de frequência ao vivo** (espectro do sinal durante o
  ensaio). É aquisição + visualização, não a suíte de análise.
- **Continua no AqDAnalysis (via TXT):** a **análise pesada** — fadiga, Rainflow, Markov, função de
  transferência, relatórios técnicos. Não reescrevemos isso.

Direção de implementação (a detalhar na fase):

- Cálculo do espectro (`rfft`) como **transformação pura**, testável no Mac sem display — mesma
  separação Presenter/Widget do [ADR-015](015-ux-e-fluxo-do-dashboard.md); o painel pyqtgraph só
  desenha. Provável dependência **numpy** (avaliar core vs. extra `[gui]`).
- Alimentado pela janela do `MonitorAoVivo` (o mesmo ring buffer do sinal×tempo).
- Critério de "funcionou": o espectro **bater** com o do AqDAnalysis/FlexLogger no mesmo sinal.

## Consequências

**Melhora:**

- Cumpre o objetivo **por inteiro** — o tio pode largar o FlexLogger no estático **e** no dinâmico.
- Diferencia de "só exportar": o valor ao vivo (ver a frequência durante o ensaio) é o que o
  FlexLogger entrega e o AqDAnalysis (pós-processamento) não.

**Piora / pendente:**

- **Escopo novo relevante:** janelamento (Hann/Hamming), resolução espectral, taxa de atualização,
  eixo em Hz — decisões da fase de implementação.
- Adiciona **numpy** (e talvez **scipy**) como dependência; definir se core ou extra.
- **Prioridade:** vem **depois** do que decide adoção (o `.exe` e a validação no hardware). É
  paridade, não pré-requisito de abrir o programa — ver [roadmap.md](../roadmap.md).
