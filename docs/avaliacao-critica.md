# Avaliação crítica — o que separa o projeto da adoção real

> **Documento de trabalho, temporário.** É a foto de uma avaliação crítica feita em **28/06/2026**,
> depois de rodar a suíte (178 testes), gerar um ensaio pela CLI, abrir o dashboard e pesquisar como
> o **FlexLogger** funciona. Serve para tratar as pendências como **urgência**. O registro
> **permanente** dessas tarefas vive em [tarefas-futuras.md](tarefas-futuras.md) e o status no
> [roadmap.md](roadmap.md) — **pode apagar este arquivo** quando as urgências estiverem endereçadas.

## Veredito

A **engenharia** está acima da média — limpa, testada, bem decidida. Mas "178 testes verdes" mede
só a parte **controlável** (código no Mac). A **meta do projeto** — o tio largar o FlexLogger — depende
inteiramente da parte **ainda não tocada**: hardware real, empacotamento e o elo com a análise dele.
O projeto está maduro no que é fácil e em ~0% no que é difícil e incerto. O risco **não está no
código**; está na distância entre o código e o uso real.

## O que está genuinamente bom (verificado, não cortesia)

- **178 testes em < 1 s, sem hardware.** A arquitetura porta/adaptador ([ADR-001](adr/001-arquitetura-porta-adaptador.md))
  não é firula — é o que torna isso possível. Decisão certa.
- **A demo gera um CSV correto** (tensão + microstrain, tempo derivado da taxa). O ciclo
  ler → converter → gravar → exportar funciona ponta a ponta.
- **O dashboard abre e funciona**: sub-plots empilhados por unidade (kgf/bar/mm/µε), XY ao vivo,
  tabela com valor instantâneo, metadata no topo, controle no rodapé.
- **A armadilha do strain está travada por teste** e o `ConfigStrain` tem defaults seguros
  (quarter-bridge 120 Ω / 2,0 V). É o maior risco técnico e está protegido.
- **Disciplina rara**: teste-guarda de AST (`nidaqmx`/`PySide6`/`openpyxl`), calibração por regressão
  como no laboratório do tio, documentação acima do normal.

Se a pergunta fosse "o código é bom?", a resposta é **sim**.

## Os gaps que importam para a meta (substituir o FlexLogger com perfeição)

### 🔴 Bloqueia a adoção hoje (sem isto, o tio não usa)

1. **Nada nunca rodou em hardware real.** Tudo é `fake` (Mac), simulado (NI-MAX) ou mock. O critério
   de "funcionou" que o próprio projeto definiu — *bater com o test panel do NI-MAX no canal real* —
   **nunca foi exercido**. Até lá, isto é uma hipótese muito bem testada, não um produto. É onde os
   sustos moram: número físico do strain, ruído de cabo longo, fiação real do 9205, célula de carga.
2. **Não existe `.exe`.** O tio não roda `pip install`. Hoje o programa **não abre na máquina dele**.
   É a Fase 6, mas é binário: sem empacotamento, adoção = 0.
3. **O TXT para o AqAnalysis nunca foi validado e é "provisório".** É o elo que deixa o tio **fazer a
   análise dele** (FFT, fadiga, laudo). Se o "Importa Arquivo Texto" não engolir o formato, ele
   adquire dados mas **não conclui o trabalho** → não substitui o fluxo. Calcanhar de Aquiles da
   estratégia "não reescrevo a análise" ([ADR-011](adr/011-estrategia-de-exportacao.md)).

### 🟠 Ameaça "fazer os ensaios com perfeição" (qualidade metrológica)

4. **Sincronização tensão × strain pendente.** O XY carga × deformação — coração da prova de carga —
   pareia dois canais que hoje vivem em **tasks separadas com offset de início** (o `zip` dos
   geradores). Para um laudo, o par (carga, deformação) tem que ser **simultâneo**. Hoje não é
   garantido. Erro que não aparece na tela mas corrompe o resultado. Precisa de *start trigger*
   compartilhado — só valida no Windows ([ADR-007](adr/007-aquisicao-continua.md)/[ADR-009](adr/009-leitura-de-strain-9235.md)).
5. **A aferição não captura a leitura ao vivo.** O painel só tem uma tabela onde o tio **digita** os
   pares (Tensão, Valor). No fluxo real (AqDados) ele aplica a carga conhecida e usa **"Leitura do
   A/D"** para pegar a tensão *daquele instante*. Sem um botão "capturar valor atual", de onde ele
   tira o número de tensão? Isso quebra o fluxo de calibração por pontos na prática.
6. **Correlação baixa não alerta.** Aceitar uma calibração ruim em silêncio, num documento
   técnico/legal, é risco metrológico. Pendência registrada no [ADR-006](adr/006-calibracao-por-pontos.md)/[ADR-017](adr/017-afericao-na-ui-e-escrita-de-config.md).

### 🟡 Gap de paridade — a meta é substituir **totalmente**

7. **Não há FFT / frequência ao vivo.** Metade do trabalho do tio é **vibração** (acelerômetro a
   1024 Hz → frequências naturais). O FlexLogger tem **Frequency Graph (FFT) ao vivo**. A estratégia
   atual é exportar pro AqDAnalysis — decisão de escopo defensável — mas significa que, **no ensaio
   dinâmico, o tio não substitui totalmente**: ainda depende de outra ferramenta para ver a
   frequência. "Substituir totalmente" e "exportar a análise" estão em leve tensão; decidir
   conscientemente (precisa de um ADR-árbitro, já anotado).
8. **Longa duração não aguenta o caso real.** Um ensaio de 1 ano a 20 Hz ≈ **630 milhões de linhas
   num único CSV** (dezenas de GB). O `carregar_csv` lê tudo em memória; não há rotação de arquivo nem
   recuperação de queda de rede do chassi Ethernet. O monitoramento de meses — que o tio **faz** — não
   é suportado de forma robusta. Arquitetural, não polimento ([ADR-012](adr/012-serie-temporal-e-exportadores.md)).

## Recomendação de foco

A próxima coisa de maior valor **não é mais código no Mac**. É **reduzir a incerteza do mundo real**:

1. **Levar ao hardware (Windows do tio) e validar UMA leitura real** contra o test panel — vale mais
   que qualquer feature nova. Guia: [guia-teste-hardware.md](guia-teste-hardware.md).
2. **Empacotar um `.exe` cedo, mesmo cru, e botar na mão do tio.** Feedback real > features no vácuo.
3. **Validar o TXT no AqAnalysis dele** (o arquivo de exemplo já foi pedido — cobrar).

Esses três *derisкam* o projeto. As features de UI (FFT ao vivo, captura de leitura na aferição,
alerta de correlação) vêm **depois**, guiadas pelo que o tio reclamar — não por adivinhação.

A verdade dura: o projeto otimizou brilhantemente a parte controlável e ainda não encarou a parte que
decide o sucesso. Tem conserto — mas o trial do FlexLogger corre, e nada acima é código bonito; é
logística e contato com o hardware.
