# Tarefas futuras — ensaios-ni

Backlog de coisas que **não bloqueiam** o trabalho atual, mas devem ser feitas quando houver
oportunidade. Só o que está **pendente** fica aqui — o que foi concluído sai do arquivo e vive no
`CHANGELOG.md`/handoff/ADR correspondente.

---

## Panorama — pendências (atualizado 07/07/2026)

Visão rápida do que falta, agrupada por **quem/o que desbloqueia**. O detalhe de cada item está nas
seções abaixo. O **levantamento de requisitos de 04/07** (imagens + áudios do tio) está resumido na
subseção *Levantamento de requisitos* logo adiante.

> **Fechados em 07/07 (saíram do backlog; ver CHANGELOG):** o **crash do editor de canais** (canal
> incompleto era gravado e derrubava o app — agora recusa antes de gravar e abre tolerante), o **botão
> "Abrir ensaio"** na tela inicial e a **exportação com duração legível + `hh:mm:ss` + trecho opcional**.

### Dependem do tio / hardware — 4 (decidem a adoção)

- **1. Validar o número físico** — NI-MAX × software, por variação carregado−repouso.
- **2. Iniciar do `.exe`** no hardware real do tio.
- **3. TXT no AqAnalysis** — importar de verdade no AqDAnalysis dele. **Feedback 04/07:** hoje "sai
  numa coluna só" e confuso; o tio quer **colunas separadas** (tempo · canal · …) com a **unidade
  embaixo do nome** e o arquivo abrindo sem atrito (ver §1 e item 9).
- **4. Erro `-200279` ao gravar** — **corrigido no código** (buffer com folga na aquisição contínua);
  **falta validar no Windows/hardware** do tio. Ver 🔴 abaixo.

### Dependem de decisão + Windows — 2

- **5. Ler em voltagem (V/V) e correlacionar** — **reforçado pelo tio (04/07):** ele *prefere* ler o
  cru em tensão/mV/V e aplicar a curva, inclusive no strain. Decide o modelo de aferição; **vira ADR**.
  Ver 🟠 abaixo.
- **6. Sincronização tensão × strain** (start-trigger).

### Dá pra fazer no Mac agora — 6

- **7. Decimal vírgula-BR** no formulário do canal — ✅ **feito (04/07)**.
- **8. Validação inline** no diálogo do canal — ✅ **feito (04/07)**.
- **9. Excel/TXT "do jeito do tio"** — colunas separadas, **unidade no cabeçalho**, metadata no topo,
  aba de resumo (junta com o §1 e o item 3).
- **10. Filtro de ruído no sinal ao vivo** — ✅ **feito (04/07):** média móvel de visualização no
  gráfico sinal×tempo (não afeta o CSV). Ver 🟡 abaixo.
- **11. Calibração "Ganho e Ponto de Referência"** *(baixa prioridade)*.
- **12. Guia de uso pro tio** (README/tutorial) — deixar **pra frente** (pedido do Weslley).

### Windows / fases futuras — 3

- **13. Parte B — discovery** de dispositivos (monta com `fake` no Mac, valida no Windows).
- **14. FFT ao vivo** (Fase 7 — a maior; **o tio confirmou o Frequency Graph do FlexLogger em 04/07**).
- **15. Robustez de longa duração** (rotação de arquivo, recuperação de queda de rede) — **estratégia
  discutida (07/07):** rotação de arquivo na gravação + concatenação no AqDAnalysis (o tio já tem) +
  Excel só por trecho; TDMS só se o volume exigir. **Aguarda o tio** dizer se faz ensaios de dias/meses
  e como resolve hoje → vira ADR. Ver 🟡 abaixo.

*(+1 condicional: parametrizar o exportador TXT — só se a validação do #3 pedir; ver §2.)*

---

## Urgências para a adoção (Fase 5–6)

> Estas pendências **decidem se o tio larga o FlexLogger** — têm prioridade sobre o resto. Por gravidade:

### Feedback de campo — teste remoto do tio (03/07/2026)

O tio rodou o software sobre o **hardware real** dele (teste proposital com **um único módulo** — o
9235/strain) e mandou o retorno por áudio. Resumo do que ele reportou:

- ✅ **Funciona:** o software **lê**, **identifica a DAQ** e **leu a deformação** que ele aplicou na
  peça (o 9235). Palavras dele: "tá fazendo tudo perfeito, só precisa refinar".
- ⚠️ **Erro recorrente ao gravar (a arrumar):** **todo início de gravação dispara um erro** logo em
  seguida, de forma repetida — apesar dele, a leitura continua ("lê bonitinho"). O **texto exato do
  erro ainda é desconhecido** (falta print/mensagem — ver pergunta ao tio). → item 🔴 abaixo.
- 🟠 **Ver/capturar a tensão no canal de strain (decisão de produto):** o botão **"Capturar tensão"
  fica cinza** no canal de strain (é o design atual — a captura ao vivo é injetada só em canais de
  tensão/9205). O tio quer ver/capturar a **tensão crua do 9235** para inserir ponto de aferição e
  **correlacionar com o test panel do NI-MAX** (que mostra V/V), inclusive para investigar o erro
  acima. → item 🟠 abaixo.
- **Não é bug:** o software "identificar só um módulo" era **esperado** — o teste usou só um módulo de
  propósito.

> A confirmar com o Weslley: se esse teste rodou o **`.exe`** ou o `python -m` — se foi o `.exe` no
> hardware real, avança o status da Fase 6 no [roadmap.md](roadmap.md). Os áudios são material do tio
> (**não versionados**, conforme [onde-pesquisar.md](onde-pesquisar.md)); só esta análise textual fica
> no repo.

### Levantamento de requisitos — imagens + áudios do tio (04/07/2026)

O tio (OFM) enviou um bloco de **imagens + áudios** como levantamento de requisitos (a pedido do
Weslley). As mídias **não** são versionadas (material do tio, [onde-pesquisar.md](onde-pesquisar.md));
só esta análise fica no repo. O que ele mostrou/pediu:

- **O erro ao gravar tem nome.** Um print do nosso software no Windows dele capturou o **DAQmx Status
  Code `-200279`** ("attempted to read samples that are no longer available… increasing the buffer
  size, reading the data more frequently, or specifying a fixed number of samples… might correct the
  problem"). É **buffer overrun** na leitura contínua — **não** é chassi/rede. Casa com o áudio ("lê
  tudo bonitinho, só dá erro depois de um tempinho"). → detalha o 🔴 abaixo.
- **Filtro de ruído.** Olhando o gráfico ruidoso do strain, pediu um **filtro** para ver o "sinal
  verdadeiro" ("tem algum filtro que passa pra tirar o ruído? consegue embutir?"). → 🟡 novo abaixo.
- **Exportação em coluna só.** O TXT "sai numa coluna só" e confuso, e não abre associado (cai no
  bloco de notas); quer **colunas separadas** (tempo · canal 0 · canal 1 · …) com a **unidade embaixo
  do nome do canal**, para montar gráficos. → §1 e item 9.
- **Prefere ler em voltagem e correlacionar.** Afere pela **leitura de tensão do canal** no AqDados e
  *prefere* ler o cru em **voltagem/mV/V** e aplicar a curva — "porque consigo fazer a curva e
  qualquer tipo de ligação (meia ponte etc.)". → 🟠 abaixo.
- **Como o FlexLogger adquire o 9235 (evidência).** As telas confirmam que os **parâmetros do strain
  batem 1:1 com os nossos** (quarter bridge, 120 Ω, internal, 2 V, **gage factor 2,14**, single
  element) e que o FlexLogger exibe **Live value (ε) + Raw value (mV/V)** lado a lado — a evidência
  direta do pedido de V/V. Mostra ainda o dashboard dele (Gauge/Meter, High Speed Graph, **Frequency
  Spectrum Graph/FFT**, XY Graph). Detalhe em [referencia-flexlogger.md §6](referencia-flexlogger.md).
  **Atenção:** isto é evidência de **requisito e de núcleo técnico**, não mandato de copiar a UX do
  FlexLogger — o espelho de produto segue o **Lynx/AqDados** ([ADR-010](adr/010-paridade-com-o-lynx.md)).

**Respostas do tio às 3 perguntas enviadas:** (1) *erro* — "lê tudo bonitinho, só dá erro depois de um
tempinho"; **não confirmou** se o CSV sai completo (sub-pendência). (2) *aferição de strain* — usa a
leitura de tensão do canal; prefere voltagem + correlação. (3) *NI-MAX* — mostra o 9235 em **µε
(strain)**, não em V/V (ainda vai conferir se dá pra ver em voltagem).

**🔴 Bloqueia a adoção (sem isto, o tio não usa):**

- [~] **Validar no hardware real** — validação **funcional** feita (29/06): o software lê o NI 9235
      real e responde à deformação. **Falta** a comparação numérica com o test panel do NI-MAX (mesma
      unidade, por **variação** carregado−repouso). Guia: [guia-teste-hardware.md](guia-teste-hardware.md). (Fase 5)
- [~] **Empacotar em `.exe`** — builda e o **`Iniciar` foi validado no simulado do NI-MAX** (02/07,
      após o fix do `copy_metadata`/`nitypes`). **Falta** o `Iniciar` no **hardware real do tio**.
      ([ADR-022](adr/022-empacotamento-exe-pyinstaller.md), Fase 6)
- [ ] **Validar o TXT no AqAnalysis** — ver §1 abaixo; é o elo da análise. Sem isto ele não fecha o
      trabalho.
- [~] **Erro `-200279` ao gravar no hardware do tio (03–04/07)** — **causa identificada** pelo print do
      levantamento (04/07): o **DAQmx Status Code `-200279`** ("attempted to read samples that are no
      longer available… increasing the buffer size, reading the data more frequently, or specifying a
      fixed number of samples to read might correct the problem") — **buffer overrun** na aquisição
      contínua do 9235 no chassi Ethernet: o nosso loop de leitura não drena o buffer circular no ritmo
      do hardware real e ele sobrescreve amostras. Aparece "depois de um tempinho" (o buffer enche); a
      leitura segue exibindo. **Só no hardware/rede real**, nunca no simulado. **Corrigido no código
      (04/07):** `_tamanho_buffer_continuo` no [daqmx.py](../src/ensaios_ni/aquisicao/daqmx.py) dá
      **folga** ao buffer de entrada (o maior entre 10× o bloco e 5 s de amostras), mantendo o `read`
      por bloco fixo — a mitigação que a própria NI recomenda. Testado por mock no Mac; **falta validar
      no Windows/hardware do tio** (o `-200279` não reproduz no simulado nem no Mac). Se persistir lá,
      escalar: bloco maior / gravação assíncrona / **thread de leitura dedicada** (possível ADR — mexe
      no modelo "passo() sem thread" do [ADR-015](adr/015-ux-e-fluxo-do-dashboard.md)). **Sub-pendências:**
      (i) confirmar com o tio se o **CSV sai completo** apesar do erro; (ii) a tradução amigável
      ([erros.py](../src/ensaios_ni/apresentacao/erros.py)) ainda mostra "confira o chassi/IP" para o
      `-200279` — o Weslley optou por **resolver a causa, não maquiar a mensagem**, então fica como
      polimento opcional. Ver [contexto-hardware.md §3](contexto-hardware.md).

**🟠 Ameaça a perfeição metrológica do laudo:**

- [ ] **Ver/capturar a tensão (razão de ponte V/V) do canal de strain (9235)** — pedido direto do tio
      (03/07), **reforçado no levantamento de 04/07**: ele *prefere* ler em voltagem e correlacionar,
      para controlar a curva e permitir outras ligações (meia ponte etc.), e o FlexLogger dele exibe
      **Live ε + Raw mV/V** ([referencia-flexlogger.md §6](referencia-flexlogger.md)). Hoje o "Capturar
      tensão" da aferição é injetado **só em canais de tensão** (9205) e fica
      **cinza** no strain, porque o 9235 entrega **strain** direto (via `add_ai_strain_gage_chan`, com
      gage factor e quarter-bridge aplicados no driver) e strain não se afere por pontos de tensão.
      **Mas há um "número de tensão" real no 9235:** o módulo é **ratiométrico** — mede a **razão de
      ponte V/V** (`Vr = (Vch/Vex)carregado − (Vch/Vex)repouso`, faixa ±29,4 mV/V), da qual o strain é
      derivado. Essa razão V/V é **o que o test panel do NI-MAX mostra** — logo, expô-la resolveria a
      **correlação NI-MAX × software** (hoje travada por unidades diferentes: V/V no NI-MAX × µε no
      software, o "ajuste fino" pendente da validação física da Fase 5) e daria ao tio o que ele pediu
      para diagnosticar o erro. Caminho técnico: ler a razão de ponte via **`BridgeUnits`/canal de bridge**
      do `nidaqmx` — **assinatura exata a confirmar contra a doc oficial e o NI-MAX no Windows** (regra:
      não inventar assinatura, [contexto-hardware.md §4](contexto-hardware.md)). **Decisão de produto
      pendente:** (a) habilitar a captura de V/V no strain (para aferição/diagnóstico), ou (b) só um
      *display* de V/V ao lado do µε, ou (c) manter cinza e explicar ao tio por que strain já vem
      calibrado. **O levantamento de 04/07 empurra para (a)/(b)** — o tio quer ver e usar o V/V.
      **Próximo passo: virar ADR** (a leitura de V/V entra na porta e muda o modelo de aferição do
      strain). Refina [ADR-017](adr/017-afericao-na-ui-e-escrita-de-config.md)/[ADR-020](adr/020-parametros-de-strain-por-canal.md).
- [ ] **Sincronização tensão × strain (start-trigger)** — o XY carga × deformação precisa dos canais
      **simultâneos**; hoje há offset entre tasks. Só valida no Windows.
      ([ADR-007](adr/007-aquisicao-continua.md)/[ADR-009](adr/009-leitura-de-strain-9235.md))

**🟡 Paridade total / robustez:**

- [x] **Filtro de ruído no sinal ao vivo (04/07)** — ✅ **feito:** `dominio/filtro.py::media_movel`
      (média móvel centrada, pura) + `QuadroAoVivo.suavizar` + controle **"Suavizar ruído"** (janela em
      pts) no rodapé do dashboard. É **só visualização** (o CSV/laudo mantém o dado cru); espelha o
      **Filtro Passa Banda** do AqDados. **Evoluções possíveis** (se o tio pedir): passa-banda de
      verdade (exigiria scipy), aplicar também no XY, escolher o tipo de filtro. Distinto do **clamp**
      (conversão) e da **remoção de outliers** (pós-processo, no AqDAnalysis).
- [~] **FFT / frequência ao vivo** — escopo decidido ([ADR-021](adr/021-fft-ao-vivo-paridade-dinamica.md)):
      FFT ao vivo no dashboard, substituindo o FlexLogger também no dinâmico. É a **Fase 7**
      ([roadmap.md](roadmap.md)), **depois** do `.exe`. Análise pesada segue no AqDAnalysis via TXT.
- [ ] **Robustez de longa duração** — rotação de arquivo + recuperação de queda de rede do chassi
      Ethernet; um ensaio de meses num único CSV é inviável (volume + memória). Inclui exportar
      ensaios gigantes (o `carregar_csv` lê o CSV inteiro em memória).
      [ADR-012](adr/012-serie-temporal-e-exportadores.md). **Estratégia discutida (07/07, aguarda o
      tio → ADR):** (1) **rotação de arquivo** na gravação (segmentar por tempo/tamanho, numerado/datado
      — cada pedaço é recuperável e cabe no Excel, que trava em ~1 M linhas ≈ 14,5 h a 20 Hz); (2)
      **juntar no AqDAnalysis** do tio, que já tem "Concatenação de Séries Temporais"
      ([referencia-lynx §2.3](referencia-lynx.md)); (3) **Excel só por trecho/resumo**, nunca o ensaio
      inteiro. **TDMS** (formato nativo NI, o que o FlexLogger usa) entra só se a taxa/volume exigir
      ([ADR-003](adr/003-persistencia-csv-do-ensaio.md) já o reservou). Perguntas enviadas ao tio (04–07/07):
      ele faz ensaios de dias/meses? como resolve hoje? que formato/extensão usa?

---

## 1. Validar o exportador TXT-AqAnalysis (formato provisório)

O exportador `txt-aqanalysis` está implementado de forma **provisória** (decimal vírgula confirmado;
separador TAB, encoding utf-8 e cabeçalho de uma linha são escolhas a confirmar). Ver
[ADR-011](adr/011-estrategia-de-exportacao.md) e o comentário no topo de
`src/ensaios_ni/persistencia/exportadores/txt_aqanalysis.py`.

> **Feedback do tio (04/07):** ao abrir a exportação, o texto "sai numa coluna só" e confuso, e o TXT
> não tem app associado (cai no bloco de notas). O que ele quer: **uma coluna por sinal** (tempo ·
> canal 0 · canal 1 · …) com a **unidade numa segunda linha de cabeçalho** (nome em cima, unidade
> embaixo), colunas separadas de verdade (TAB), para montar gráficos. Reforça o **cabeçalho de duas
> linhas** e a checagem de separador/decimal — e conecta com o item 9 (Excel/TXT "do jeito do tio").
> Ainda **não** foi importado no AqDAnalysis de verdade (as vias A/B abaixo seguem valendo).

Como fechar (qualquer uma das vias valida):

- [ ] **Via A — TXT legítimo do tio.** O tio exporta um TXT qualquer no AqDAnalysis e envia. Com um
      arquivo real em mãos, comparo o layout (separador, encoding, cabeçalho, nomes de unidade) e
      ajusto o exportador para casar. **O Weslley já pediu o arquivo a ele (25/06/2026) e aguarda.**
- [ ] **Via B — testar na casa do tio.** Ir ao computador do tio (Fase 5, junto da calibração
      física) e tentar **importar o nosso TXT** no AqDAnalysis dele. Ajustar separador/decimal/
      cabeçalho no wizard de importação. É o teste definitivo (o critério de "funcionou").

> Expectativa fundamentada: o "Importa Arquivo Texto" do AqDAnalysis é quase certamente um **wizard
> configurável** (escolhe separador/decimal e aponta as colunas). Se for, não há "formato secreto":
> o nosso TXT limpo + a escolha do tio no wizard bastam.

## 2. Plano B — parametrizar o exportador TXT

Se a validação (tarefa 1) mostrar que o AqDAnalysis precisa de uma variante diferente, em vez de
fixar um novo formato, **tornar o `txt-aqanalysis` parametrizável**:

- [ ] separador configurável (`;` / TAB / espaço);
- [ ] separador decimal configurável (vírgula / ponto);
- [ ] opção de incluir a **taxa de amostragem no cabeçalho** (alguns importadores ASCII usam isso
      para reconstruir o eixo de tempo/frequência).

Implementar **só quando a validação indicar necessidade** — não especular antes.

---

## 3. Configuração de canais na UI ([ADR-023](adr/023-configuracao-de-canais-na-ui.md)) — em andamento

O tio não deve editar o `canais.toml` à mão. Design fechado no ADR-023: biblioteca de **perfis**
`.toml` gerenciada pelo app + **editor** de canais na tela + **discovery** dos dispositivos atrás da
porta. Fatiado; estado atual:

**Parte A — no Mac:**

- [x] **A1 — Biblioteca de perfis.** A tela inicial lista os ensaios salvos (`~/ensaios-ni/*.toml`) e
      abre o escolhido. (`apresentacao/perfis.py` + `TelaInicial`.)
- [x] **A2 — Editor de canais.** Tabela de canais na UI (Adicionar/Editar/Remover) + formulário por
      canal, persistindo no `.toml`. (`apresentacao/editor_canais.py` + `qt/editor_canais.py`.)
- [x] **A3 — Gerência de perfis (completa, 04/07).** Criar, Importar, Renomear, Remover, Duplicar e
      Exportar — todos pela tela, com validação de nome e erros de domínio
      (`PerfilJaExiste`/`PerfilNaoExiste`/`NomeDePerfilInvalido`/`ImportacaoInvalida`). **Fecha a
      Parte A do [ADR-023](adr/023-configuracao-de-canais-na-ui.md)** (biblioteca + editor + gerência);
      a biblioteca não nasce mais vazia numa máquina nova.

**Parte B — precisa do Windows (hardware/simulado):**

- [ ] **B — Discovery de dispositivos.** Porta de inventário (`daqmx` lista `System.local().devices`;
      `fake` lista sintética) + botão "Detectar canais" que preenche a tabela do editor. Só depois do
      feedback do tio ([ADR-019](adr/019-foco-em-validacao-fisica-e-adocao.md)).

**Refinamentos menores da A2** (não bloqueiam):

- [x] **Botão "Editar canais…" não dava feedback sem perfil selecionado** (descoberto no Windows,
      03/07; **corrigido em 04/07**). O botão nasce **desabilitado** e habilita ao selecionar um
      ensaio (`currentItemChanged` → `_sincronizar_botoes`), como o "Aferir".
- [x] **UX da tela inicial com muitos botões** — **resolvido (04/07):** a tela foi reorganizada em
      **dois grupos** (ações do ensaio selecionado × ações da biblioteca/avulso), em vez de uma fileira
      única. Resta a ambiguidade menor entre "Importar…" (adota na biblioteca) e "Abrir configuração…"
      (abre avulso) — aceitável por ora; fundir num fluxo só é opção futura, não bloqueia.
- [x] Exibir os números do formulário do canal em **decimal vírgula (BR)** — ✅ feito (04/07); o parse
      já aceitava vírgula e ponto, agora a exibição também usa vírgula.
- [x] Validação **inline** no diálogo (Aplicar só habilita com endereço + unidade) — ✅ feito (04/07);
      substituiu o popup pós-clique.

---

## Outras pendências conhecidas (menores)

- [ ] **Guia de uso dentro do app para o tio (README/tutorial)** — instruções em linguagem leiga de
      como operar o programa (criar/importar ensaio, editar canais, aferir, tarar, iniciar, exportar),
      acessível **de dentro do app** (ex.: botão "Ajuda"/"Como usar") ou junto do `.exe`. Complementa o
      `LEIA.txt` do [pacote-tio](pacote-tio/README.md), que hoje só cobre abrir o programa. **Para mais
      pra frente** (pedido do Weslley, 04/07) — não agora.
- [ ] **Excel/TXT "do jeito do tio"** — **colunas separadas de verdade** (tempo · canal · …) com a
      **unidade embaixo do nome** (cabeçalho de duas linhas), metadata no cabeçalho (obra, data,
      sensor, taxa) e aba de resumo. **Feedback 04/07:** o arquivo "sai numa coluna só" e confuso (ver
      §1). Camada de entrega, a definir com o gosto dele. [ADR-011](adr/011-estrategia-de-exportacao.md).
- [ ] **Calibração "Ganho e Ponto de Referência"** — segundo modo de aferição do AqDados; redutível
      ao linear, baixa prioridade. [ADR-006](adr/006-calibracao-por-pontos.md).
