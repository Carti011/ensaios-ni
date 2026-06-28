from dataclasses import dataclass


@dataclass(frozen=True)
class Metadata:
    """Cabeçalho de rastreabilidade do ensaio (vira laudo) — ADR-018.

    Espelha os campos do relatório do AqDAnalysis (referencia-lynx §2.4). Todos opcionais.
    """

    obra: str = ""
    operador: str = ""
    data: str = ""
    observacao: str = ""
