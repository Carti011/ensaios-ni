# ADR 013 — Stack do dashboard (Fase 4)

## Status

**Aceito** (26/06/2026). Stack escolhida: **PyQt6/PySide6 + pyqtgraph** (opção A). O Weslley
priorizou a **adoção do tio** (desktop como o AqDados, `.exe` fácil de instalar, tempo real de
verdade) sobre o portfólio web — e ganha o aprendizado de uma stack nova.

> **Atualização (26/06/2026):** o binding foi fixado em **PySide6** (LGPL, oficial da Qt) por causa
> da distribuição em `.exe` fechado — ver [ADR-015](015-ux-e-fluxo-do-dashboard.md), que também
> define a UX e o fluxo de telas.

## Contexto

A Fase 4 ([roadmap.md](../roadmap.md)) é a interface gráfica — o que torna o software usável pelo
tio. Restrições do caso:

- **Roda local** no Windows do tio (não é web hospedada; é um usuário, uma máquina).
- **Tempo real é requisito do domínio:** prova de carga (XY carga×deformação ao vivo) e vibração
  (até 1024 Hz, FFT). O sinal precisa aparecer **durante** o ensaio.
- **Backend é Python** (`nidaqmx` só existe em Python) — a UI tem que conversar com ele.
- **O tio é leigo em TI:** precisa **abrir como um programa** (idealmente um `.exe`), não rodar
  `pip` nem subir servidor.
- **Referência mental do tio:** AqDados/FlexLogger/LabVIEW — todos **desktop**.
- **Peso do portfólio:** o Weslley registrou no brief que o projeto vale como peça de portfólio.

## Opções avaliadas

### A) PyQt6 / PySide6 + pyqtgraph — *app desktop nativo*

- **Prós:** é um **programa de verdade** (igual ao que o tio já usa); **pyqtgraph é o padrão-ouro de
  plot científico em tempo real** em Python (feito para DAQ, aguenta alta taxa); integra **direto**
  com o backend Python (mesmo processo, sem API/rede); empacota em **`.exe` com PyInstaller**
  (instalação trivial). É a que melhor serve a **adoção pelo tio**.
- **Contras:** UI menos "web moderna"; portfólio é de **engenharia de instrumentação**, não web dev;
  curva do PyQt (signals/slots, layouts).

### B) React + FastAPI — *web moderno*

- **Prós:** UI mais flexível e profissional; **melhor portfólio web** (stack vendável); streaming
  via websocket é sólido.
- **Contras:** **~2× o trabalho** (duas linguagens, build, dois processos); **distribuição local
  ruim** (servir build + backend + navegador numa máquina de um usuário leigo); complexidade
  desproporcional para um app local.

### C) Plotly Dash — *web local em Python*

- **Prós:** Python puro, rápido de prototipar, gráficos bonitos, reusa o backend.
- **Contras:** roda como **servidor web + navegador** (estranho para "um programa"); **tempo real de
  alta taxa é fraco** (callbacks/Interval) — justo o requisito crítico; empacotar em `.exe` é chato.

## Decisão (recomendação)

**Recomendo a opção A — PyQt6/PySide6 + pyqtgraph.** O critério de sucesso do projeto é a **adoção
pelo tio**, e essa stack é a que melhor serve: desktop local como ele está acostumado, `.exe`
trivial de instalar, tempo real de verdade (pyqtgraph), e zero camada de rede entre UI e aquisição.
O portfólio que ela gera (instrumentação/DAQ com hardware real) é diferenciado por si só — o projeto
já é raro independentemente da UI ser web.

**Quando reconsiderar para a B (React+FastAPI):** se o Weslley priorizar **portfólio web** acima da
facilidade de adoção, aceitando ~2× o trabalho e uma distribuição local mais complexa. A **C (Dash)**
fica como protótipo rápido se a meta for só "ver algo na tela já", mas não a recomendo para o
produto por causa do tempo real.

> **Decidido:** opção **A (PyQt6/PySide6 + pyqtgraph)**. A Fase 4 começa pelo **design/UX**
> (planejar o fluxo antes de codar tela), não pela implementação — em outra sessão.

## Consequências

- **Se A:** add `PySide6`/`pyqtgraph` como extra (ex.: `[gui]`); a UI roda no mesmo processo do
  backend; distribuição vira um alvo PyInstaller. O domínio testável no Mac **não muda** (a porta
  `FonteDeAquisicao` já isola tudo); a UI desktop fica numa camada `apresentacao/`.
- **Se B:** novo subprojeto frontend (React) + uma API (FastAPI) expondo a porta por websocket; dois
  ciclos de build; mais superfície para testar.
- Em qualquer caso, a arquitetura porta/adaptador (ADR-001) já deixa a aquisição pronta para ser
  consumida por qualquer UI — a escolha **não** afeta o backend já feito.
