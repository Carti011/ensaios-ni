"""Launcher do dashboard ligado ao hardware real (NI-DAQmx) — Fase 5.

Diferente da demo (`janela.abrir()`, adaptador `fake`), este entrypoint monta a
`JanelaMonitor` sobre o `AdaptadorDaqmx`, lendo os canais reais do `canais.toml`.
Roda só no Windows (o `nidaqmx` é carregado lazy dentro do adaptador). Repassa
canais + config à janela para que Aferir e os rótulos funcionem no hardware.
"""

import argparse
import tomllib
from pathlib import Path

from ensaios_ni.apresentacao.monitor import MonitorAoVivo
from ensaios_ni.apresentacao.qt.janela import JanelaMonitor
from ensaios_ni.aquisicao.daqmx import AdaptadorDaqmx
from ensaios_ni.dominio.canais import carregar_canais
from ensaios_ni.dominio.erros import CanalNaoConfigurado, ConfiguracaoInvalida


def montar_janela(
    config: Path,
    taxa_hz: float,
    bloco: int,
    saida: Path,
    capacidade_janela: int | None = None,
) -> JanelaMonitor:
    canais = carregar_canais(config)
    fonte = AdaptadorDaqmx(canais=canais)
    monitor = MonitorAoVivo(
        fonte, canais, taxa_hz, bloco, Path(saida), capacidade_janela=capacidade_janela
    )
    return JanelaMonitor(monitor, canais=canais, caminho_config=Path(config))


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="ensaios_ni.apresentacao.qt.hardware",
        description="Abre o dashboard ao vivo ligado ao hardware NI (Windows).",
    )
    parser.add_argument("--config", type=Path, required=True, help="canais.toml com os canais reais")
    parser.add_argument("--taxa", type=float, default=1024.0, help="taxa de amostragem em Hz")
    parser.add_argument("--bloco", type=int, default=256, help="amostras por bloco (streaming)")
    parser.add_argument("--saida", type=Path, default=Path("ensaio.csv"),
                        help="CSV onde o ensaio é gravado")
    parser.add_argument("--capacidade-janela", type=int, default=2000,
                        help="pontos exibidos no gráfico (janela deslizante p/ ensaios longos)")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = _parse_args(argv)
    try:
        janela = montar_janela(
            args.config, args.taxa, args.bloco, args.saida,
            capacidade_janela=args.capacidade_janela,
        )
    except FileNotFoundError:
        raise SystemExit(f"config não encontrado: {args.config}") from None
    except (ConfiguracaoInvalida, CanalNaoConfigurado, tomllib.TOMLDecodeError) as erro:
        raise SystemExit(f"config inválido: {erro}") from None
    _exibir(janela)


def _exibir(janela: JanelaMonitor) -> None:  # pragma: no cover — abre a UI (bloqueia no exec)
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    janela.resize(1000, 600)
    janela.show()
    app.exec()


if __name__ == "__main__":  # pragma: no cover
    main()
