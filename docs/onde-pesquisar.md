# Onde pesquisar — protocolo de dúvida e filosofia de produto

> Leia isto **antes de perguntar ao Weslley** ou de inventar uma solução.
> A maioria das dúvidas de produto e de domínio já tem resposta numa fonte conhecida.

## O que este software é (e o que não é)

Este software **substitui o FlexLogger** — a única peça **paga** da pilha do tio (NI-DAQmx e NI-MAX
são gratuitos). **Não substitui o AqDAnalysis**: a análise (FFT, fadiga, relatórios) continua sendo
feita lá pelo tio; nós interoperamos exportando dados (ver [ADR-011](adr/011-estrategia-de-exportacao.md)).

**Não é uma cópia do FlexLogger nem do AqDados.** A meta não é clonar — é **fazer melhor** e
**caber no uso do tio**, que já domina o AqDados/AqDAnalysis. Concretamente, três camadas com
exigências diferentes:

| Camada | Regra | Por quê |
| ------ | ----- | ------- |
| **Núcleo técnico** — como o número é calculado, calibrado e armazenado (escala, regressão, clamp, taxa, formato de dado) | **Siga o padrão de mercado.** Não invente. Tem que ser metrologicamente correto e o tio tem que poder usar **profissionalmente** no serviço dele. | Um laudo de prova de carga vale como documento técnico/legal. Errar a calibração ou o método é inaceitável. O padrão existe (NI-DAQmx, metrologia, normas) — siga-o. |
| **Fluxo e vocabulário** — como o tio opera (aferição, balanço/repouso, tabela de canais, nomes) | **Espelhe o AqDados/AqDAnalysis.** É o que ele domina há anos. | Adoção: ele larga o software pago só se reconhecer o nosso. Ver [ADR-010](adr/010-paridade-com-o-lynx.md). |
| **Produto e entrega** — UX, exportação, conveniências | **Aqui a gente MELHORA e ADAPTA ao gosto do tio.** É o nosso diferencial sobre o FlexLogger. | Ex.: exportar Excel do jeito que encaixa no trabalho dele; UX mais moderna; menos passos. "Da maneira que o FlexLogger faz, **com adendos**." |

Resumo: **núcleo técnico = seguir o padrão; fluxo = espelhar o tio; entrega = superar o FlexLogger.**

## Princípio norteador

O **usuário final é o tio** (OFM Engenharia — instrumentação e análise experimental de estruturas:
pontes, viadutos, lajes; strain gages, LVDTs, acelerômetros, células de carga que ele mesmo
**fabrica e calibra** com rastreabilidade INMETRO/RBC). Não é o Weslley nem nós. O que importa
**não** é o Weslley concordar com uma decisão — é o **tio conseguir trabalhar** com confiança
profissional. Em dúvida entre "do nosso jeito" e "do jeito que o mercado/o tio faz", escolha o
segundo no núcleo técnico e no fluxo; reserve a criatividade para a camada de entrega.

## Tipo de dúvida → onde procurar

| Dúvida é sobre… | Fonte interna (1º) | Fonte externa (2º) |
| --------------- | ------------------ | ------------------ |
| **Produto / UX / terminologia / fluxo** (como o tio calibra, nomeia, organiza canais, analisa) | [referencia-lynx.md](referencia-lynx.md), [CONTEXT.md](../CONTEXT.md) | Lynx — manuais/datasheets do AqDados/AqDAnalysis: <https://www.lynxtec.com.br/softwares.htm> |
| **Técnica do driver / aquisição** (NI-DAQmx: escala, timing, sample clock, strain/ponte, simulados) | [contexto-hardware.md](contexto-hardware.md) (**API pinada**), [referencia-flexlogger.md](referencia-flexlogger.md) | NI: <https://www.ni.com> (NI-DAQmx, FlexLogger). **NI-MAX test panel** = critério objetivo de "funcionou" (a leitura tem que bater com ele) |
| **Padrão de mercado / metrologia** (como calibrar, curva de calibração, formato de dado, rastreabilidade) | [referencia-flexlogger.md](referencia-flexlogger.md) (Custom Scales), [adr/006](adr/006-calibracao-por-pontos.md) | Normas que o tio cita: **NBR 6118, 7188, 8800, 14931, 14762, AWS D1.1, ISO 6892-1**; metrologia (regressão linear, linearidade, INMETRO/RBC) |
| **Domínio / engenharia** (que ensaios o tio faz, grandezas, sensores) | [respostas-tio.md](respostas-tio.md), memória `dominio-do-tio-ofm` | **Site da OFM**: <https://ofmengenharia.com.br> — código no cofre em `codigo/ofm-engenharia/` (ver `components/AcervoTecnico.tsx` e `data/servicos-detalhados.tsx`) |
| **Decisões já tomadas** (por que algo é como é) | [docs/adr/](adr/) | — |
| **Qualquer dúvida sem fonte clara** | — | **Pesquisa no Google** é fonte legítima — use sempre que ajudar (o Weslley autorizou), registrando o que achou |

> **Produto vs técnica (a regra do [ADR-010](adr/010-paridade-com-o-lynx.md)):** o **AqDados/AqDAnalysis
> (Lynx)** é o espelho de **produto** (o que o tio usa e domina). O **FlexLogger/NI-DAQmx** é
> referência **técnica do driver**. Em conflito de comportamento de produto, vale o Lynx; em
> comportamento do driver, vale o NI-DAQmx.

## Protocolo

1. **Classifique** a dúvida (núcleo técnico, fluxo, entrega, domínio, decisão).
2. **Consulte a fonte interna** da tabela. Quase tudo que o tio enviou já está resumido lá.
3. Se não bastar, **a fonte externa** correspondente — inclusive **Google** quando fizer sentido.
4. **Aplique a camada certa:** núcleo técnico/fluxo → siga o padrão (não invente); entrega → melhore
   e adapte ao tio.
5. **Registre o que descobriu** na referência interna certa (`referencia-lynx.md`,
   `referencia-flexlogger.md`, `respostas-tio.md`). Se virar decisão de arquitetura, abra um **ADR**.
6. **Só leve ao Weslley** o que as fontes não resolvem **ou** o que é decisão de produto/escopo dele
   (prioridade, o que entra em cada fase, gosto de UX/exportação). Dúvida técnica ou de padrão,
   **resolva pela fonte**.

## Quando o tio enviar material novo (prints, áudios, arquivos)

- Os prints têm dados de clientes → **não versionar** (ficam em `docs/img/`, ignorada). Só a análise
  textual entra no repo.
- Extraia o aprendizado para `referencia-lynx.md` (produto) ou `respostas-tio.md` (domínio) e
  atualize o `CONTEXT.md` se surgir vocabulário novo.
