from dataclasses import dataclass

from ensaios_ni.aquisicao.porta import FonteDeAquisicao


def _carregar_nidaqmx():
    # import lazy: nidaqmx só existe no Windows/Linux x86. Este é o ÚNICO
    # arquivo autorizado a importá-lo (ver docs/adr/001 e teste-guarda).
    import nidaqmx
    from nidaqmx.constants import AcquisitionType, TerminalConfiguration

    return nidaqmx, AcquisitionType, TerminalConfiguration


def _carregar_nidaqmx_strain():
    import nidaqmx
    from nidaqmx.constants import (
        AcquisitionType,
        ExcitationSource,
        StrainGageBridgeType,
        StrainUnits,
    )

    return nidaqmx, AcquisitionType, ExcitationSource, StrainGageBridgeType, StrainUnits


@dataclass(frozen=True)
class ConfigStrain:
    """Parâmetros do 9235 (quarter-bridge 120 Ω, excitação interna 2,0 V).

    Os DEFAULTS aqui são os do 9235 — JAMAIS os da API NI (full-bridge 350 Ω / 2,5 V),
    que produzem número plausível e errado sem lançar erro. Ver contexto-hardware §4.
    """

    gage_factor: float = 2.15  # meio da faixa 2,14–2,16; varia por lote do extensômetro
    nominal_gage_resistance: float = 120.0
    voltage_excit_val: float = 2.0
    bridge_config: str = "QUARTER_BRIDGE_I"
    poisson_ratio: float = 0.3
    lead_wire_resistance: float = 0.0  # 3 fios compensa; ajustar para cabo longo
    min_val: float = -0.001
    max_val: float = 0.001


class AdaptadorDaqmx(FonteDeAquisicao):
    """Adaptador real sobre o NI-DAQmx. Lê tensão (9205) e strain (9235). Roda só no Windows."""

    def __init__(
        self,
        terminal_config: str = "DIFF",
        min_val: float = -10.0,
        max_val: float = 10.0,
        config_strain: ConfigStrain | None = None,
    ):
        self._terminal_config = terminal_config
        self._min_val = min_val
        self._max_val = max_val
        self._config_strain = config_strain or ConfigStrain()

    def ler_tensao(
        self, canais: list[str], amostras: int, taxa_hz: float
    ) -> dict[str, list[float]]:
        nidaqmx, AcquisitionType, TerminalConfiguration = _carregar_nidaqmx()

        with nidaqmx.Task() as task:
            for canal in canais:
                task.ai_channels.add_ai_voltage_chan(
                    canal,
                    terminal_config=getattr(TerminalConfiguration, self._terminal_config),
                    min_val=self._min_val,
                    max_val=self._max_val,
                )
            # sample clock explícito: o 9235 (delta-sigma) no chassi Ethernet
            # falha sem timing; os 9205 também usam, por consistência.
            task.timing.cfg_samp_clk_timing(
                rate=taxa_hz,
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=amostras,
            )
            dados = task.read(number_of_samples_per_channel=amostras)

        return self._normalizar(canais, dados)

    def ler_strain(
        self, canais: list[str], amostras: int, taxa_hz: float
    ) -> dict[str, list[float]]:
        nidaqmx, AcquisitionType, ExcitationSource, StrainGageBridgeType, StrainUnits = (
            _carregar_nidaqmx_strain()
        )
        cfg = self._config_strain

        with nidaqmx.Task() as task:
            for canal in canais:
                # parâmetros do 9235 — NUNCA os defaults da API (full-bridge 350 Ω / 2,5 V)
                task.ai_channels.add_ai_strain_gage_chan(
                    canal,
                    strain_config=getattr(StrainGageBridgeType, cfg.bridge_config),
                    voltage_excit_source=ExcitationSource.INTERNAL,
                    voltage_excit_val=cfg.voltage_excit_val,
                    nominal_gage_resistance=cfg.nominal_gage_resistance,
                    gage_factor=cfg.gage_factor,
                    poisson_ratio=cfg.poisson_ratio,
                    lead_wire_resistance=cfg.lead_wire_resistance,
                    initial_bridge_voltage=0.0,
                    units=StrainUnits.STRAIN,
                    min_val=cfg.min_val,
                    max_val=cfg.max_val,
                )
            # 9235 (delta-sigma) no chassi Ethernet exige sample clock explícito
            task.timing.cfg_samp_clk_timing(
                rate=taxa_hz,
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=amostras,
            )
            dados = task.read(number_of_samples_per_channel=amostras)

        return self._normalizar(canais, dados)

    @staticmethod
    def _normalizar(canais: list[str], dados) -> dict[str, list[float]]:
        # task.read devolve lista simples para 1 canal e lista de listas para vários.
        if len(canais) == 1:
            return {canais[0]: list(dados)}
        return {canal: list(coluna) for canal, coluna in zip(canais, dados)}
