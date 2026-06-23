from ensaios_ni.aquisicao.porta import FonteDeAquisicao


def _carregar_nidaqmx():
    # import lazy: nidaqmx só existe no Windows/Linux x86. Este é o ÚNICO
    # arquivo autorizado a importá-lo (ver docs/adr/001 e teste-guarda).
    import nidaqmx
    from nidaqmx.constants import AcquisitionType, TerminalConfiguration

    return nidaqmx, AcquisitionType, TerminalConfiguration


class AdaptadorDaqmx(FonteDeAquisicao):
    """Adaptador real sobre o NI-DAQmx. Lê tensão dos 9205. Roda só no Windows."""

    def __init__(
        self,
        terminal_config: str = "DIFF",
        min_val: float = -10.0,
        max_val: float = 10.0,
    ):
        self._terminal_config = terminal_config
        self._min_val = min_val
        self._max_val = max_val

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

    @staticmethod
    def _normalizar(canais: list[str], dados) -> dict[str, list[float]]:
        # task.read devolve lista simples para 1 canal e lista de listas para vários.
        if len(canais) == 1:
            return {canais[0]: list(dados)}
        return {canal: list(coluna) for canal, coluna in zip(canais, dados)}
