"""File utility functions."""

from pathlib import Path


def ensure_directory(path: Path | str) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory.

    Returns:
        The Path object.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_files(
    directory: Path | str,
    extensions: list[str] | None = None,
    recursive: bool = False,
) -> list[Path]:
    """List files in a directory, optionally filtering by extension.

    Args:
        directory: Directory to search.
        extensions: Optional list of extensions to filter by (e.g., [".pdf", ".md"]).
        recursive: Whether to search recursively.

    Returns:
        List of file paths.
    """
    directory = Path(directory)

    if not directory.exists():
        return []

    if recursive:
        files = list(directory.rglob("*"))
    else:
        files = list(directory.iterdir())

    # Filter to files only
    files = [f for f in files if f.is_file()]

    # Filter by extensions if specified
    if extensions:
        extensions = [ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions]
        files = [f for f in files if f.suffix.lower() in extensions]

    return sorted(files)


def get_file_extension(path: Path | str) -> str:
    """Get the file extension (lowercase, with dot).

    Args:
        path: Path to the file.

    Returns:
        The file extension (e.g., ".pdf").
    """
    return Path(path).suffix.lower()


def is_pdf(path: Path | str) -> bool:
    """Check if a file is a PDF.

    Args:
        path: Path to the file.

    Returns:
        True if the file has a .pdf extension.
    """
    return get_file_extension(path) == ".pdf"


def is_markdown(path: Path | str) -> bool:
    """Check if a file is a Markdown file.

    Args:
        path: Path to the file.

    Returns:
        True if the file has a .md or .markdown extension.
    """
    return get_file_extension(path) in (".md", ".markdown")


def safe_filename(name: str) -> str:
    """Convert a string to a safe filename.

    Args:
        name: The original name.

    Returns:
        A sanitized filename.
    """
    # Replace problematic characters
    replacements = {
        "/": "-",
        "\\": "-",
        ":": "-",
        "*": "",
        "?": "",
        '"': "",
        "<": "",
        ">": "",
        "|": "",
    }

    result = name
    for old, new in replacements.items():
        result = result.replace(old, new)

    # Remove leading/trailing whitespace and dots
    result = result.strip(". ")

    # Limit length
    if len(result) > 200:
        result = result[:200]

    return result or "untitled"
