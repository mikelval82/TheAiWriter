"""CLI entry points for the background citation judge and the plugin version."""

import argparse
from pathlib import Path

from ai_writer import __version__
from ai_writer.library import LibraryError


def main(argv: list[str] | None = None) -> None:
    """Dispatch the public CLI, including the invocation used by ``start_judge``."""
    parser = argparse.ArgumentParser(
        prog="ai-writer", description="Verifica citas de documentos basados en Zotero."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("version", help="Muestra la versión del plugin")
    document = commands.add_parser("documento", help="Verifica un documento")
    actions = document.add_subparsers(dest="action", required=True)
    verify = actions.add_parser("verificar", help="Ejecuta el juez de apoyo de las citas")
    verify.add_argument(
        "folder", nargs="?", default=Path("."), type=Path, help="Carpeta del documento"
    )
    args = parser.parse_args(argv)
    if args.command == "version":
        print(f"TheAIWriter {__version__}")
        return

    from ai_writer import verificacion

    try:
        data = verificacion.run_judge(args.folder)
    except LibraryError as error:
        parser.exit(1, f"{error}\n")
    print(verificacion.summary(data["apoyo"]))


if __name__ == "__main__":
    main()
