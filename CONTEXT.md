# CONTEXT — ensaios-ni

Glossário do domínio. Mantém linguagem consistente entre código, docs e conversas.
Termos físicos (hardware/extensometria) e termos de software (arquitetura).

## Glossário — hardware

- **Chassi / cDAQ** — o **NI cDAQ-9184**, "corpo" CompactDAQ de 4 slots com conexão Ethernet. Não mede nada sozinho: dá timing, alimentação e conexão aos módulos. No código: identificado pelo nome que o NI-MAX atribui (ex.: `cDAQ9184-1820306`).
- **Módulo C Series** — placa que entra num slot do chassi e faz a medição de fato. Temos três. No NI-MAX viram `Mod1`, `Mod2`, `Mod3` (no simulado, `cDAQ1Mod1`…).
- **NI 9205** — módulo de **entrada de tensão**. 32 canais single-ended / 16 diferenciais, ±200 mV a ±10 V, 16 bits. Temos **dois**. Lê LVDT, acelerômetro e outros sensores de saída em tensão.
- **NI 9235** — módulo de **strain gauge** (extensometria). 8 canais, quarter-bridge, completação de 120 Ω embutida, excitação interna fixa de 2,0 V, 24 bits. Temos **um**. Delta-sigma: exige sample clock explícito no chassi Ethernet.
- **Canal físico** — entrada concreta de um módulo (ex.: `Mod1/ai0`). É o endereço de onde o sinal entra.
- **Tensão** — grandeza crua lida pelo 9205, em volts. Quase nunca é o resultado final: precisa virar unidade de engenharia.
- **Strain / deformação / extensometria** — medida adimensional de quanto um material deforma sob carga, lida pelo 9235. Saída em **microstrain**. Sinônimos no projeto.
- **Quarter-bridge** — topologia de ligação do extensômetro usada pelo 9235 (um gauge ativo + completação interna). No código: `StrainGageBridgeType.QUARTER_BRIDGE_I`.
- **Three-wire (3 fios)** — ligação do extensômetro com 3 vias (22 AWG no setup do dono) para compensar a resistência de **cabo longo**. Relevante na config da task de strain.
- **Gage factor** — fator de sensibilidade do extensômetro. No setup do dono **varia de 2,14 a 2,16** por lote → parâmetro configurável, nunca fixo. Errar = strain errado e silencioso.
- **Excitação** — tensão que alimenta o sensor/ponte. No 9235 é **interna e fixa em 2,0 V**; o 9205 **não excita** (acelerômetro usa 5 V de alimentação externa).
- **Tara / null / zero** — leitura de offset com a peça em repouso, no início do ensaio, declarada como zero. No strain: `initial_bridge_voltage`. É etapa fixa do fluxo do dono.
- **Calibração por pontos** — método real de conversão do dono: aplica carga conhecida, lê a voltagem e **monta a curva voltagem→engenharia ponto a ponto** (como o canal de calibração do AqDados). Ver [ADR-006](docs/adr/006-calibracao-por-pontos.md). O `ganho·V+offset` linear é o caso de 2 pontos.
- **Unidade de engenharia** — o número que importa pro dono (microstrain, kgf, mm, MPa…). Resultado da **conversão/calibração** aplicada sobre tensão/strain crus.
- **LVDT** — sensor de **deslocamento** (mm), lido como tensão no 9205.
- **Acelerômetro** — sensor de **vibração** (aceleração), sensibilidade 2G, alimentado por 5 V externos, lido no 9205. É o sensor da vibração a 1024 Hz.
- **Célula de carga** — sensor de **força** (kgf). Só liga no 9205 se tiver saída em tensão condicionada (a placa não excita ponte crua) — a confirmar com o dono.
- **Ensaio** — uma sessão de medição com começo, fim e propósito físico. Dura de 1 h a **1 ano contínuo** (monitoramento). O "resultado" que precisa ser registrado e exibido.

## Glossário — software

- **NI-DAQmx** — driver **gratuito** da NI que conversa com o hardware. É a camada que o LabVIEW/FlexLogger usavam por baixo. Roda só em Windows/Linux x86.
- **`nidaqmx`** — pacote Python oficial (PyPI), wrapper sobre o driver. Como nosso código fala com o hardware.
- **NI-MAX** — ferramenta **gratuita** da NI onde o chassi é descoberto, nomeado e testado (test panel). Continua em uso.
- **FlexLogger** — aplicação **paga (assinatura)** da NI para configurar ensaios, registrar e calibrar. **É o que este projeto substitui.** O dono paga por ela hoje.
- **AqDados (Lynx)** — software de **aquisição** multicanal do dono (config de canais, calibração de sensores, gravação em tempo real). Referência funcional, inclusive do canal de calibração por pontos.
- **AqDAnalysis (Lynx)** — software de **análise** do dono (tempo/frequência, filtros digitais, relatórios). Referência para a Fase 3/análise (FFT). Compatibilizar formato de arquivo é meta.
- **Dispositivo simulado** — chassi/módulos virtuais criados no NI-MAX que devolvem dados sintéticos. Roda **só no Windows**. Valida o adaptador real sem o hardware. **Não** é teste unitário.
- **Task** — unidade central do DAQmx: conjunto de canais + timing + trigger. Tensão e strain são tipos diferentes → **tasks separadas**. Os dois 9205 dividem uma task; o 9235 fica em task própria. Exige `cfg_samp_clk_timing` (sample clock) — obrigatório para o 9235 no chassi Ethernet.
- **Aquisição** — o ato de ler amostras do hardware. Isolada atrás de uma porta. Hoje **finita** (lê N e para); evoluirá para **contínua** ([ADR-007](docs/adr/007-aquisicao-continua.md)).
- **FonteDeAquisicao (porta)** — interface que o resto do sistema conhece. `ler_tensao(canais, amostras, taxa_hz) -> dict` — **multi-canal**, lê todos sob o mesmo sample clock (alinhados no tempo). Ver [ADR-001](docs/adr/001-arquitetura-porta-adaptador.md) e [ADR-005](docs/adr/005-contrato-multicanal-da-porta.md).
- **Adaptador DAQmx (`daqmx.py`)** — implementação real da porta (tensão pronta; strain pendente). **Único** arquivo que importa `nidaqmx`, lazy. Roda só no Windows.
- **Adaptador Fake (`fake.py`)** — implementação sintética da porta. Roda em qualquer lugar (inclusive Mac). Habilita o TDD do domínio.
- **Conversão** — transforma tensão/strain cru em unidade de engenharia. Linear por config (`config/canais.toml`) hoje; evoluindo para **calibração por pontos + tara** ([ADR-006](docs/adr/006-calibracao-por-pontos.md)). Nunca hardcode.

## Conceitos centrais

O equipamento do dono é um sistema de **aquisição de dados de ensaios mecânicos**: sensores (células de carga, LVDTs, acelerômetros, extensômetros) ligados aos módulos NI, que digitalizam sinais elétricos. Hoje isso depende de software pago (FlexLogger/LabVIEW). **O acesso ao hardware nunca foi a parte paga** — o driver NI-DAQmx e o NI-MAX são grátis. O projeto substitui apenas a **camada de aplicação**: ler os canais, converter pra unidade física e registrar/exibir o ensaio.

A dificuldade **não é o código de leitura** — é converter o sinal bruto na grandeza física correta. Essa informação (qual sensor em cada canal, calibração, gage factor) está com o dono, não no equipamento, e ele a obtém por **calibração empírica por pontos**. Por isso a conversão é configuração/calibração externa, e o critério de "funcionou" é bater com o test panel do NI-MAX.
