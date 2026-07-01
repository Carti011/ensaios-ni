from collections.abc import Callable, Sequence
from pathlib import Path

from ensaios_ni.dominio.erros import RegressaoIndeterminada
from ensaios_ni.dominio.regressao import Reta, ajustar_regressao
from ensaios_ni.persistencia.config_canais import salvar_afericao


class Afericao:
    """Presenter da aferição de um canal (Fase 4, fatia 3 — ADR-015/006).

    Espelha a "Aferição por Regressão Linear" do AqDados: o usuário monta a tabela de pontos
    `(volts, valor de engenharia)` e a aferição ajusta uma única reta a eles (mínimos quadrados),
    reportando a correlação. `aplicar()` persiste a calibração no TOML. Python puro, sem PySide —
    testável no Mac sem display.
    """

    def __init__(
        self,
        caminho: Path | None = None,
        canal: str = "",
        pontos: Sequence[tuple[float, float]] = (),
        capturar: Callable[[], float] | None = None,
    ) -> None:
        self._caminho = Path(caminho) if caminho is not None else None
        self._canal = canal
        self._pontos: list[tuple[float, float]] = [(float(v), float(val)) for v, val in pontos]
        self._capturar = capturar

    @property
    def pode_capturar(self) -> bool:
        """Há uma fonte de leitura ao vivo ligada (canal de tensão com hardware/fake)."""
        return self._capturar is not None

    def capturar_tensao(self) -> float | None:
        """Lê a tensão que o canal está gerando agora (o "Leitura do A/D"). None se indisponível."""
        if self._capturar is None:
            return None
        return self._capturar()

    @property
    def pontos(self) -> list[tuple[float, float]]:
        return list(self._pontos)

    def adicionar_ponto(self, volts: float, valor: float) -> None:
        self._pontos.append((float(volts), float(valor)))

    def definir_pontos(self, pontos: Sequence[tuple[float, float]]) -> None:
        self._pontos = [(float(volts), float(valor)) for volts, valor in pontos]

    def remover_ponto(self, indice: int) -> None:
        del self._pontos[indice]

    def reta(self) -> Reta | None:
        # < 2 pontos ou tensão sem variação (estado transitório ao montar a tabela): sem reta
        if len(self._pontos) < 2:
            return None
        try:
            return ajustar_regressao(self._pontos)
        except RegressaoIndeterminada:
            return None

    def ganho_inverso(self) -> float | None:
        """O "Ganho K" do AqDados (V/unidade) = inverso de `reta.a`. None sem reta ou se `a` for 0."""
        reta = self.reta()
        if reta is None or reta.a == 0:
            return None
        return 1.0 / reta.a

    def correlacao_percentual(self) -> str:
        """Qualidade do ajuste como o AqDados mostra ("100,00 %"), em decimal vírgula (BR)."""
        reta = self.reta()
        if reta is None:
            return "—"
        return f"{abs(reta.correlacao) * 100:.2f} %".replace(".", ",")

    def aplicar(self) -> None:
        """Persiste a aferição no TOML do canal. Exige ao menos 2 pontos (uma reta)."""
        if self._caminho is None:
            raise ValueError("aferição sem arquivo de destino: informe caminho e canal")
        if len(self._pontos) < 2:
            raise ValueError("aferição precisa de ao menos 2 pontos para ajustar a reta")
        salvar_afericao(self._caminho, self._canal, self._pontos)
