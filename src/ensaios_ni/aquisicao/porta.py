from abc import ABC, abstractmethod
from collections.abc import Iterator


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

    @abstractmethod
    def ler_strain(
        self, canais: list[str], amostras: int, taxa_hz: float
    ) -> dict[str, list[float]]:
        """Lê `amostras` de strain (adimensional) dos canais informados.

        Task separada da tensão (tipo de medição diferente). O driver já aplica
        gage factor e ponte, devolvendo strain adimensional; a conversão para
        microstrain (×1.000.000) é do domínio. Devolve canal → lista de strain.
        """
        ...

    @abstractmethod
    def transmitir_tensao(
        self, canais: list[str], taxa_hz: float, amostras_por_bloco: int
    ) -> Iterator[dict[str, list[float]]]:
        """Transmite tensão em fluxo contínuo, emitindo um bloco por vez.

        Modo de aquisição contínua (ADR-007): em vez de ler N amostras e parar,
        produz blocos de `amostras_por_bloco` indefinidamente, sob o mesmo sample
        clock. O consumidor decide quando parar (fechando o gerador encerra a task).
        """
        ...

    @abstractmethod
    def transmitir_strain(
        self, canais: list[str], taxa_hz: float, amostras_por_bloco: int
    ) -> Iterator[dict[str, list[float]]]:
        """Transmite strain em fluxo contínuo, emitindo um bloco por vez. Task separada da tensão."""
        ...
