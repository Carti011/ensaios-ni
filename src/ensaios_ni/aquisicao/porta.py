from abc import ABC, abstractmethod


class FonteDeAquisicao(ABC):
    """Porta de aquisição. O resto do sistema depende só desta interface.

    Implementada por dois adaptadores: o real (`daqmx`, Windows, único que
    importa `nidaqmx`) e o `fake` (sintético, roda no Mac).
    """

    @abstractmethod
    def ler_tensao(self, canal: str, amostras: int) -> list[float]:
        """Lê `amostras` de tensão (volts brutos) do canal físico informado."""
        ...
