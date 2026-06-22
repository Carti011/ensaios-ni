import argparse
from pathlib import Path

from ensaios_ni.aplicacao.demo import executar_demonstracao
from ensaios_ni.aplicacao.ensaio import executar_ensaio
from ensaios_ni.aquisicao.daqmx import AdaptadorDaqmx
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
    parser.add_argument("--amostras", type=int, default=100, help="amostras por canal")
    parser.add_argument("--saida", type=Path, default=Path("ensaio-demo.csv"))
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = _parse_args(argv)

    if args.fonte == "fake":
        executar_demonstracao(
            args.saida, amostras=args.amostras, taxa_hz=args.taxa, caminho_config=args.config
        )
    else:
        if args.config is None:
            raise SystemExit("--config é obrigatório com --fonte daqmx")
        canais = carregar_canais(args.config)
        executar_ensaio(AdaptadorDaqmx(), canais, args.amostras, args.taxa, args.saida)

    print(f"Ensaio gravado em: {args.saida.resolve()}")


if __name__ == "__main__":
    main()
