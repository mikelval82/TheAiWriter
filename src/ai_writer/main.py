"""CLI entry points for background checks, reviews and the plugin version."""

import argparse
from pathlib import Path

from ai_writer import __version__
from ai_writer.library import LibraryError


def main(argv: list[str] | None = None) -> None:
    """Dispatch the public CLI and the background processes."""
    parser = argparse.ArgumentParser(
        prog="ai-writer", description="Verifica y revisa documentos basados en Zotero."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("version", help="Muestra la versión del plugin")
    document = commands.add_parser("documento", help="Verifica o revisa un documento")
    actions = document.add_subparsers(dest="action", required=True)
    verify = actions.add_parser("verificar", help="Ejecuta el juez de apoyo de las citas")
    verify.add_argument(
        "folder", nargs="?", default=Path("."), type=Path, help="Carpeta del documento"
    )
    review = actions.add_parser("revisar", help="Evalúa el borrador por criterios sin cambiarlo")
    review.add_argument(
        "folder", nargs="?", default=Path("."), type=Path, help="Carpeta del documento"
    )
    args = parser.parse_args(argv)
    if args.command == "version":
        print(f"TheAIWriter {__version__}")
        return

    from ai_writer import revisor, verificacion

    try:
        if args.action == "revisar":
            data = revisor.run_review(args.folder)
            print(data["estado"])
        else:
            data = verificacion.run_judge(args.folder)
            print(verificacion.support_summary(data))
    except LibraryError as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
