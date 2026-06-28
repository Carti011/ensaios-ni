from collections.abc import Sequence
from dataclasses import dataclass
from math import sqrt

from ensaios_ni.dominio.erros import RegressaoIndeterminada


@dataclass(frozen=True)
class Reta:
    """Reta de calibração ajustada a pontos: `valor = a * volts + b`, com a correlação do ajuste."""

    a: float
    b: float
    correlacao: float

    def aplicar(self, volts: float) -> float:
        return self.a * volts + self.b


def ajustar_regressao(pontos: Sequence[tuple[float, float]]) -> Reta:
    """Ajusta uma única reta a N pontos `(volts, valor)` por mínimos quadrados.

    Espelha a "Aferição por Regressão Linear" do AqDados: tolera ruído de medição
    (a reta não passa por cada ponto) e reporta a **correlação** de Pearson (R) como
    qualidade do ajuste. Quando não há dispersão (resíduo zero), a correlação é 1,0.
    """
    n = len(pontos)
    soma_x = sum(x for x, _ in pontos)
    soma_y = sum(y for _, y in pontos)
    soma_xy = sum(x * y for x, y in pontos)
    soma_xx = sum(x * x for x, _ in pontos)
    soma_yy = sum(y * y for _, y in pontos)

    var_x = n * soma_xx - soma_x * soma_x
    var_y = n * soma_yy - soma_y * soma_y
    cov_xy = n * soma_xy - soma_x * soma_y

    if var_x == 0:  # tensão sem variação: reta vertical, coeficiente indeterminado
        raise RegressaoIndeterminada(
            "pontos sem variação de tensão (volts): a reta de calibração é indeterminada"
        )
    a = cov_xy / var_x
    b = (soma_y - a * soma_x) / n
    correlacao = 1.0 if var_y == 0 else cov_xy / sqrt(var_x * var_y)
    return Reta(a=a, b=b, correlacao=correlacao)
