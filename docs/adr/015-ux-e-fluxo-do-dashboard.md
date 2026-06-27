# ADR 015 — UX e fluxo do dashboard (Fase 4)

## Status

**Aceito** (26/06/2026). Refina o [ADR-013](013-stack-do-dashboard.md) (que decidiu a stack
PyQt6/PySide6 + pyqtgraph): este ADR **fixa o binding em PySide6** e define a **UX e o fluxo de
telas** da Fase 4. Produto deste ADR é um **design brief** de discovery — guia a implementação,
não a substitui.

## Contexto

A Fase 4 ([roadmap.md](../roadmap.md)) é a interface gráfica — o que torna o software usável pelo
tio (OFM Engenharia), que **domina o AqDados/AqDAnalysis (Lynx)** e só está aprendendo o FlexLogger
(trial pago). Critério de sucesso do projeto: **ele largar o FlexLogger e adotar o nosso**. A
filosofia de produto (ver [onde-pesquisar.md](../onde-pesquisar.md)) tem três camadas: **núcleo
técnico** segue o padrão de mercado, **fluxo/vocabulário** espelha o tio (AqDados), **entrega
(UX)** a gente melhora.

O backend (Fases 0–3) está completo e isolado atrás da porta `FonteDeAquisicao` (ADR-001): a UI
só consome `ler_tensao`/`ler_strain` e `transmitir_tensao`/`transmitir_strain`. Roda no Mac com o
adaptador `fake`; Windows só na Fase 5.

Decisões de produto tomadas com o Weslley na sessão de discovery (`/planejar-ux`, 26/06/2026):
estrutura de janela, tema, grau de modernidade do visual e por onde começar.

## Decisão

### Binding: PySide6 (LGPL), não PyQt6

O ADR-013 listava "PyQt6/PySide6". Fica **PySide6**: é o binding **oficial da Qt** e é **LGPL** —
permite empacotar e distribuir um **`.exe` fechado** (Fase 6, PyInstaller) sem as amarras da GPL do
PyQt6 (que exigiria abrir o código ou licença comercial paga). Tecnicamente equivalentes (muda o
`import` e `Signal` no lugar de `pyqtSignal`); o `pyqtgraph` suporta os dois.

### Direção de design: claro, denso, técnico — moderno e minimalista

- **Tema claro, alta densidade** (estilo planilha/instrumentação): familiar pro tio e legível sob
  luz do dia em campo (pontes, lajes).
  > **Atualização (fatia 1, 26/06):** na prática o **gráfico** (pyqtgraph) usa fundo claro e o
  > *chrome* (tabela, botões, fundo) **segue o tema do SO** — escuro no macOS do dev, claro no
  > Windows do tio. O Weslley aprovou esse visual na fatia 1; **não** fixamos um QSS claro. Reavaliar
  > só se o tio preferir tudo claro.
- **Moderno e minimalista** ("o simples que funciona"): sem skeumorfismo nem decoração; grid
  alinhado, tipografia **tabular/mono** nos números, **decimal vírgula (BR)**. Um **acento de cor
  único** reservado ao estado "adquirindo".
- **Vocabulário do Lynx em PT** (Aferição, Balanço/Repouso, Tara, Correlação, Consulta, Sinal,
  Canal) — ver [referencia-lynx.md](../referencia-lynx.md). Herda-se **comportamento e vocabulário**,
  não o visual Windows-clássico.

### Estrutura: workspace de painéis (janela única)

```text
┌──────────────────────────────────────────────────────────┐
│ ensaios-ni     obra: ____   operador: ____   fonte: fake ▾│  ← cabeçalho/metadata
├───────────────┬──────────────────────────────────────────┤
│ CANAIS        │  SINAL × TEMPO            (área herói)    │
│ ☑ ai0  µε  ·· │   ╱╲   ╱╲   ╱╲                            │
│ ☑ ai1  kgf ·· │  ╱  ╲ ╱  ╲ ╱                              │
│ ☐ ai2  mm  ·· │ ──────────────────────────────────────   │
│               │  XY  carga × deformação                  │
│ [Aferir…]     │   · · · · · ·                            │
├───────────────┴──────────────────────────────────────────┤
│ ▶ Iniciar  ■ Parar   ⏱ 00:42  ▦ 43 008 am.  20 Hz   ● ADQ │  ← barra de controle
└──────────────────────────────────────────────────────────┘
```

- **Esquerda** — painel de canais: nome, unidade, tipo, **valor ao vivo**, checkbox de exibição
  (à la AqDados). Botão **Aferir** por canal.
- **Centro/direita (herói)** — gráficos pyqtgraph: sinal×tempo + XY carga×deformação.
- **Rodapé** — controle do ensaio sempre visível: Iniciar/Parar, cronômetro, contagem de amostras,
  taxa, estado.
- **Topo** — metadata do ensaio (obra, data, operador) para rastreabilidade do laudo.

### Ação primária

**Ver o sinal do ensaio ao vivo, com confiança de que o número está certo.** Configurar, aferir e
exportar orbitam isso.

### Estados

- **Sem config**: CTA "Abrir configuração de canais" (`.toml`).
- **Config carregada / parado**: tabela populada, eixos prontos, gráfico vazio, Iniciar habilitado.
- **Adquirindo**: traço correndo, valores atualizando, cronômetro/contador subindo, indicador no
  acento de cor, só Parar disponível.
- **Parado pós-ensaio**: dados congelados, CSV já gravado (`GravadorEnsaioCsv`), Exportar disponível.
- **Erro** (TOML inválido / canal inexistente / fonte indisponível, ex.: `daqmx` no Mac): mensagem
  amigável, **sem traceback** (padrão já no backend).
- **Edge — ensaio longo** (1 ano @ 20 Hz): **janela deslizante** de visualização (ring
  buffer/downsampling), nunca plotar tudo. **Muitos canais**: empilhar com scroll.

### Modelo de interação

Abrir config → marcar canais → **Iniciar** dispara thread de aquisição que consome `transmitir_*`
da porta e emite blocos por **signal/slot** (a UI nunca trava) → pyqtgraph atualiza com
downsampling → **Parar** encerra limpo → **Exportar** reusa os exportadores (formato + sinais +
janela). Aferição: seleciona canal → painel com tabela de pontos `(V, valor eng.)`, regressão,
**correlação %** e tara → aplica e persiste no TOML.

### Plano de fatias (vertical, TDD)

1. **Monitor ao vivo** — workspace mínimo: carrega TOML (canais read-only) → `fake` transmite →
   sinal×tempo correndo → Parar/grava CSV. *De-risca o tempo real, entrega o coração.*
2. **XY + multicanal** — carga×deformação, seleção de canais, empilhamento.
3. **Aferição na UI** — tabela de canais editável + painel de calibração (pontos/regressão/
   correlação/tara), persistindo no TOML.
4. **Metadata + Exportar na UI** — cabeçalho do ensaio + reuso dos exportadores.

## Consequências

- Nova camada `src/ensaios_ni/apresentacao/` (ainda não existe). O backend **não muda**: a porta
  já entrega tudo (ADR-001); a UI só consome. Domínio segue testável no Mac.
- Add `PySide6` + `pyqtgraph` como extra (ex.: `[gui]`) no `pyproject`. Distribuição vira um alvo
  PyInstaller (Fase 6).
- **Pendências abertas** (resolver na fatia correspondente):
  - **FFT ao vivo vs. exportar pro AqDAnalysis** — tensão entre a visão de futuro e o
    [ADR-011](011-estrategia-de-exportacao.md); precisa de um **ADR-árbitro** quando chegar na
    visualização de vibração. Fora do MVP.
  - **Escrever TOML** preservando comentários pede `tomlkit` (o `tomllib` é só leitura) — afeta a
    fatia 3.
  - **Metadata do ensaio** (obra/operador) hoje não existe na persistência → extensão de backend,
    em commit separado da UI.
  - **Threading**: `QThread` + signals vs. `QTimer` puxando do iterador — decidir na fatia 1.
- O critério de sucesso continua sendo a **adoção pelo tio**; cada fatia é medida contra
  "ele reconhece e consegue usar".
