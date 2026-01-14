"""PDF document reader using PyMuPDF."""

from pathlib import Path

import fitz  # PyMuPDF


class PDFReader:
    """Reader for extracting text from PDF documents."""

    def read(self, path: Path | str) -> str:
        """Read and extract text from a PDF file.

        Args:
            path: Path to the PDF file.

        Returns:
            Extracted text content from the PDF.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is not a valid PDF.
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"File is not a PDF: {path}")

        text_parts = []

        with fitz.open(path) as doc:
            for page_num, page in enumerate(doc, 1):
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"--- Page {page_num} ---\n{text}")

        return "\n\n".join(text_parts)

    def read_pages(self, path: Path | str, start: int = 1, end: int | None = None) -> str:
        """Read specific pages from a PDF file.

        Args:
            path: Path to the PDF file.
            start: Starting page number (1-indexed).
            end: Ending page number (inclusive). None means until the end.

        Returns:
            Extracted text from the specified pages.
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        text_parts = []

        with fitz.open(path) as doc:
            total_pages = len(doc)
            end = end or total_pages

            # Adjust for 0-based indexing
            for page_num in range(start - 1, min(end, total_pages)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

        return "\n\n".join(text_parts)

    def get_metadata(self, path: Path | str) -> dict:
        """Extract metadata from a PDF file.

        Args:
            path: Path to the PDF file.

        Returns:
            Dictionary containing PDF metadata.
        """
        path = Path(path)

        with fitz.open(path) as doc:
            metadata = doc.metadata
            metadata["page_count"] = len(doc)
            return metadata
