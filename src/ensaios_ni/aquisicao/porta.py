from abc import ABC, abstractmethod


class FonteDeAquisicao(ABC):
    """Porta de aquisição. O resto do sistema depende só desta interface.

    Implementada por dois adaptadores: o real (`daqmx`, Windows, único que
    importa `nidaqmx`) e o `fake` (sintético, roda no Mac).
    """

    @abstractmethod
    def ler_tensao(
        self, canais: list[str], amostras: int, taxa_hz: float
    ) -> dict[str, list[float]]:
        """Lê `amostras` de tensão (volts brutos) dos canais informados.

        Lê todos os canais numa única task, amostrados pelo mesmo sample clock
        (`taxa_hz`), para que fiquem alinhados no tempo. Devolve um dicionário
        canal → lista de volts.
        """
        ...
