# ADR 019 — Foco em validação física e adoção; documentação de campo unificada

## Status

Aceito (28/06/2026). Não altera código nem decisões de arquitetura anteriores — registra uma
**decisão de direção** (onde gastar esforço a partir daqui) e a reorganização da documentação que
ela motivou.

## Contexto

Com a **Fase 4 concluída** (ver [roadmap.md](../roadmap.md)), o backend e o dashboard estão completos
e cobertos por 178 testes no Mac. Uma avaliação crítica desta sessão (registrada em
[avaliacao-critica.md](../avaliacao-critica.md)) deixou claro um descompasso: **"178 testes verdes"
mede a parte controlável (código no Mac), mas o critério de sucesso do projeto — o tio largar o
FlexLogger — depende inteiramente da parte ainda não tocada**:

- **Nada nunca rodou em hardware real.** O critério objetivo de "funcionou" (bater com o test panel
  do NI-MAX) nunca foi exercido.
- **Não existe `.exe`.** O tio não roda `pip install`; hoje o programa não abre na máquina dele.
- **O TXT para o AqAnalysis nunca foi validado** — é o elo que fecha o ciclo de análise dele.

Some-se a isso uma desorganização da documentação operacional: `guia-windows.md` (instalação) e
`validacao-windows.md` (validação no NI-MAX **simulado**) se sobrepunham em público e momento, e o
caso simulado já cumpriu seu papel (Fase 2). Faltava um guia que levasse **do ambiente zerado ao
ensaio validado no hardware real**.

## Decisão

1. **A prioridade passa a ser reduzir a incerteza do mundo real, não somar features no Mac.** A
   ordem de maior valor é: (a) validar **uma leitura real** contra o test panel; (b) empacotar um
   **`.exe`** e pôr na mão do tio; (c) validar o **TXT** no AqAnalysis dele. Features de UI (FFT ao
   vivo, captura de leitura na aferição, alerta de correlação) vêm **depois**, guiadas pelo feedback
   do tio — ver as **Urgências** em [tarefas-futuras.md](../tarefas-futuras.md).
2. **A documentação de teste vira um guia único de campo:** [guia-teste-hardware.md](../guia-teste-hardware.md)
   (Fase 5), do ambiente ao ensaio validado, com o caso simulado como variante. Os antigos
   `guia-windows.md` e `validacao-windows.md` foram **fundidos** nele. Aplica o [ADR-014](014-fonte-unica-na-documentacao.md)
   (fonte única): um dono por informação, os demais apontam.
3. **A avaliação crítica fica registrada em dois lugares com papéis distintos:** um documento de
   trabalho **temporário** ([avaliacao-critica.md](../avaliacao-critica.md), removível quando as
   urgências fecharem) e o backlog **permanente** ([tarefas-futuras.md](../tarefas-futuras.md), seção
   "Urgências para a adoção").

## Consequências

**Melhora:**

- O esforço passa a atacar o que **decide o sucesso** (hardware, distribuição, interoperabilidade),
  não o que já está maduro.
- Um único guia de campo torna a ida ao hardware do tio um roteiro linear, com checklist e
  troubleshooting.
- A documentação volta a ter um dono por informação (some a sobreposição dos dois guias Windows).

**Piora / pendente:**

- As três urgências 🔴 dependem de **acesso ao hardware/Windows do tio** — fora do Mac, fora do
  controle direto do dev. O cronômetro do trial do FlexLogger corre.
- O guia de campo descreve passos que **só serão exercidos de verdade na Fase 5** — pode precisar de
  ajuste depois do primeiro contato com o hardware real (é esperado).
- A tensão **FFT ao vivo vs. exportar para o AqAnalysis** segue aberta (paridade total com o
  FlexLogger no ensaio dinâmico) e ainda pede um ADR-árbitro quando chegar a vez da vibração.
