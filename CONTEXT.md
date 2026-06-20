# CONTEXT — ensaios-ni

Glossário do domínio. Mantém linguagem consistente entre código, docs e conversas.
Termos físicos (hardware/extensometria) e termos de software (arquitetura).

## Glossário — hardware

- **Chassi / cDAQ** — o **NI cDAQ-9184**, "corpo" CompactDAQ de 4 slots com conexão Ethernet. Não mede nada sozinho: dá timing, alimentação e conexão aos módulos. No código: identificado pelo nome que o NI-MAX atribui (ex.: `cDAQ9184-1820306`).
- **Módulo C Series** — placa que entra num slot do chassi e faz a medição de fato. Temos três. No NI-MAX viram `Mod1`, `Mod2`, `Mod3`.
- **NI 9205** — módulo de **entrada de tensão**. 32 canais single-ended / 16 diferenciais, ±200 mV a ±10 V, 16 bits. Temos **dois**. São os "condicionadores" que o tio mencionou.
- **NI 9235** — módulo de **strain gauge** (extensometria). 8 canais, quarter-bridge, completação de 120 Ω embutida, excitação interna fixa de 2,0 V, 24 bits. Temos **um**.
- **Canal físico** — entrada concreta de um módulo (ex.: `Mod1/ai0`). É o endereço de onde o sinal entra.
- **Tensão** — grandeza crua lida pelo 9205, em volts. Quase nunca é o resultado final: precisa virar unidade de engenharia.
- **Strain / deformação / extensometria** — medida adimensional de quanto um material deforma sob carga, lida pelo 9235. Unidade `strain` (ou microstrain). Sinônimos no projeto.
- **Quarter-bridge** — topologia de ligação do extensômetro usada pelo 9235 (um gauge ativo + completação interna). No código: `StrainGageBridgeType.QUARTER_BRIDGE_I`.
- **Gage factor** — fator de sensibilidade do extensômetro. Vem do datasheet do gauge, **não** do módulo. Errar = strain errado e silencioso.
- **Excitação** — tensão que o módulo aplica na ponte pra medir. No 9235 é **interna e fixa em 2,0 V**.
- **Nulling / zero** — leitura de offset com a peça em repouso, antes do ensaio, pra zerar a deformação inicial. No código: parâmetro `initial_bridge_voltage`.
- **Unidade de engenharia** — o número que importa pro tio (kgf, bar, °C, mm, microstrain…). Resultado da **conversão** aplicada sobre tensão/strain crus.
- **Ensaio** — uma sessão de medição com começo, fim e propósito físico. O "resultado" que precisa ser registrado e exibido.

## Glossário — software

- **NI-DAQmx** — driver **gratuito** da NI que conversa com o hardware. É a camada que o LabVIEW/FlexLogger usavam por baixo. Roda só em Windows/Linux x86.
- **`nidaqmx`** — pacote Python oficial (PyPI), wrapper sobre o driver. Como nosso código fala com o hardware.
- **NI-MAX** — ferramenta gratuita da NI onde o chassi é descoberto, nomeado e testado (test panel). Continua em uso; some é só o FlexLogger/LabVIEW.
- **Dispositivo simulado** — chassi/módulos virtuais criados no NI-MAX que devolvem dados sintéticos. Roda **só no Windows**. Serve pra validar o adaptador real sem o hardware. **Não** é teste unitário.
- **Task** — unidade central do DAQmx: conjunto de canais + timing + trigger. Cria, configura, lê, fecha. Tensão e strain são tipos diferentes → **tasks separadas**. Os dois 9205 podem dividir uma task; o 9235 fica em task própria.
- **Aquisição** — o ato de ler amostras do hardware. No projeto, isolada atrás de uma porta.
- **FonteDeAquisicao (porta)** — interface que o resto do sistema conhece. Define `ler_tensao()` / `ler_strain()` sem saber se por trás está hardware real ou fake. Ver [ADR-001](docs/adr/001-arquitetura-porta-adaptador.md).
- **Adaptador DAQmx (`daqmx.py`)** — implementação real da porta. **Único** arquivo que importa `nidaqmx`. Roda só no Windows.
- **Adaptador Fake (`fake.py`)** — implementação sintética da porta. Roda em qualquer lugar (inclusive Mac). Habilita o TDD do domínio.
- **Conversão** — função pura que transforma tensão/strain cru em unidade de engenharia, parametrizada por **config** (`config/canais.toml`), nunca hardcode.

## Conceitos centrais

O equipamento do tio é um sistema de **aquisição de dados de ensaios mecânicos**: sensores (células de carga, transdutores, extensômetros) ligados aos módulos NI, que digitalizam sinais elétricos. Hoje isso só funciona via software pago (LabVIEW/FlexLogger). O acesso ao hardware nunca foi a parte paga — o driver NI-DAQmx é grátis. O projeto substitui apenas a **camada de aplicação**: ler os canais, converter pra unidade física e registrar/exibir o ensaio.

A dificuldade do projeto **não é o código de leitura** — é converter o sinal bruto na grandeza física correta. Essa informação (qual sensor em cada canal, fórmula de conversão, gage factor) está com o dono do hardware, não no equipamento. Por isso a conversão é tratada como configuração externa, e o critério de "funcionou" é bater com o test panel do NI-MAX.
