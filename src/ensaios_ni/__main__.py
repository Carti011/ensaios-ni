import argparse
import signal
from pathlib import Path

from ensaios_ni.aplicacao.demo import _CONFIG_EXEMPLO, _sinais_sinteticos, executar_demonstracao
from ensaios_ni.aplicacao.ensaio import executar_ensaio, executar_ensaio_continuo
from ensaios_ni.aquisicao.daqmx import AdaptadorDaqmx
from ensaios_ni.aquisicao.fake import AquisicaoFake
from ensaios_ni.dominio.canais import carregar_canais


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="ensaios_ni",
        description="Roda um ensaio: lê os canais, converte para unidade e grava em CSV.",
    )
    parser.add_argument("--fonte", choices=["fake", "daqmx"], default="fake",
                        help="fake (sintético, Mac) ou daqmx (hardware/simulado, Windows)")
    parser.add_argument("--config", type=Path, default=None,
                        help="canais.toml (obrigatório com --fonte daqmx)")
    parser.add_argument("--taxa", type=float, default=100.0, help="taxa de amostragem em Hz")
    parser.add_argument("--amostras", type=int, default=100, help="amostras por canal (modo finito)")
    parser.add_argument("--amostras-tara", type=int, default=0,
                        help="amostras de repouso para tara/zero por canal (0 = sem tara)")
    parser.add_argument("--continuo", action="store_true",
                        help="aquisição contínua (streaming por blocos) até a duração ou Ctrl-C")
    parser.add_argument("--duracao-s", type=float, default=None,
                        help="duração do ensaio contínuo em segundos (sem isso, vai até Ctrl-C)")
    parser.add_argument("--bloco", type=int, default=100,
                        help="amostras por bloco no modo contínuo")
    parser.add_argument("--saida", type=Path, default=Path("ensaio-demo.csv"))
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = _parse_args(argv)

    if args.continuo:
        _rodar_continuo(args)
    elif args.fonte == "fake":
        executar_demonstracao(
            args.saida, amostras=args.amostras, taxa_hz=args.taxa, caminho_config=args.config
        )
    else:
        if args.config is None:
            raise SystemExit("--config é obrigatório com --fonte daqmx")
        canais = carregar_canais(args.config)
        executar_ensaio(
            AdaptadorDaqmx(), canais, args.amostras, args.taxa, args.saida,
            amostras_tara=args.amostras_tara,
        )

    print(f"Ensaio gravado em: {args.saida.resolve()}")


def _rodar_continuo(args) -> None:
    canais = carregar_canais(args.config) if args.config else carregar_canais(_CONFIG_EXEMPLO)
    if args.fonte == "fake":
        # sinal sintético cobrindo a duração pedida (default 1 s) + um bloco de folga
        amostras = int((args.duracao_s or 1.0) * args.taxa) + args.bloco
        tensoes, strains = _sinais_sinteticos(canais, amostras, args.taxa)
        fonte = AquisicaoFake(tensoes=tensoes, strains=strains)
    else:
        if args.config is None:
            raise SystemExit("--config é obrigatório com --fonte daqmx")
        fonte = AdaptadorDaqmx()

    with _parada_por_ctrl_c() as parar:
        executar_ensaio_continuo(
            fonte, canais, args.taxa, args.saida, args.bloco,
            amostras_tara=args.amostras_tara, duracao_s=args.duracao_s, parar=parar,
        )


class _parada_por_ctrl_c:
    """Liga o Ctrl-C (SIGINT) a um sinal de parada limpo; restaura o handler ao sair."""

    def __enter__(self):
        self._interrompido = False
        self._anterior = None
        try:
            self._anterior = signal.signal(signal.SIGINT, self._capturar)
        except ValueError:
            pass  # fora da main thread: segue sem captura de Ctrl-C
        return lambda: self._interrompido

    def _capturar(self, signum, frame):
        self._interrompido = True

    def __exit__(self, *exc):
        if self._anterior is not None:
            signal.signal(signal.SIGINT, self._anterior)
        return False


if __name__ == "__main__":
    main()
