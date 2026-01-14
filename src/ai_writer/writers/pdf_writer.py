"""PDF document writer using PyMuPDF."""

from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF

from ai_writer.models.paper import Paper


class PDFWriter:
    """Writer for exporting papers to PDF format."""

    def __init__(
        self,
        font_size: int = 11,
        title_size: int = 18,
        heading_size: int = 14,
        margin: int = 72,  # 1 inch in points
    ) -> None:
        """Initialize the PDF writer.

        Args:
            font_size: Base font size for body text.
            title_size: Font size for the main title.
            heading_size: Font size for section headings.
            margin: Page margins in points.
        """
        self.font_size = font_size
        self.title_size = title_size
        self.heading_size = heading_size
        self.margin = margin

    def write(self, paper: Paper, path: Path | str) -> Path:
        """Write a paper to a PDF file.

        Args:
            paper: The paper to export.
            path: Path where to save the file.

        Returns:
            Path to the created file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        doc = fitz.open()
        self._generate_pdf(doc, paper)
        doc.save(str(path))
        doc.close()

        return path

    def _generate_pdf(self, doc: fitz.Document, paper: Paper) -> None:
        """Generate PDF content from a paper.

        Args:
            doc: The PDF document to write to.
            paper: The paper to convert.
        """
        # Page dimensions (Letter size)
        page_width = 612
        page_height = 792

        # Create first page
        page = doc.new_page(width=page_width, height=page_height)

        # Content area
        content_width = page_width - 2 * self.margin
        y_position = self.margin

        # Insert title
        y_position = self._insert_text(
            page,
            paper.title,
            y_position,
            self.title_size,
            bold=True,
            center=True,
        )
        y_position += 20

        # Insert authors
        if paper.authors:
            authors_str = ", ".join(paper.authors)
            y_position = self._insert_text(
                page,
                authors_str,
                y_position,
                self.font_size,
                center=True,
            )
            y_position += 10

        # Insert date
        date_str = datetime.now().strftime("%B %d, %Y")
        y_position = self._insert_text(
            page,
            date_str,
            y_position,
            self.font_size,
            center=True,
        )
        y_position += 30

        # Insert sections
        for section in paper.sections:
            # Check if we need a new page
            if y_position > page_height - self.margin - 100:
                page = doc.new_page(width=page_width, height=page_height)
                y_position = self.margin

            # Section heading
            y_position = self._insert_text(
                page,
                section.title,
                y_position,
                self.heading_size,
                bold=True,
            )
            y_position += 10

            # Section content - split into paragraphs
            paragraphs = section.content.split("\n\n")
            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue

                # Check if we need a new page
                if y_position > page_height - self.margin - 50:
                    page = doc.new_page(width=page_width, height=page_height)
                    y_position = self.margin

                y_position = self._insert_text(
                    page,
                    paragraph.strip(),
                    y_position,
                    self.font_size,
                )
                y_position += 10

            y_position += 15  # Space between sections

    def _insert_text(
        self,
        page: fitz.Page,
        text: str,
        y_position: float,
        font_size: int,
        bold: bool = False,
        center: bool = False,
    ) -> float:
        """Insert text into the page and return the new y position.

        Args:
            page: The page to insert text into.
            text: The text to insert.
            y_position: Starting Y position.
            font_size: Font size to use.
            bold: Whether to use bold font.
            center: Whether to center the text.

        Returns:
            The Y position after inserting the text.
        """
        page_width = page.rect.width
        content_width = page_width - 2 * self.margin

        # Create text rect
        if center:
            rect = fitz.Rect(self.margin, y_position, page_width - self.margin, y_position + 200)
        else:
            rect = fitz.Rect(self.margin, y_position, page_width - self.margin, y_position + 500)

        # Choose font
        font_name = "helv" if not bold else "hebo"

        # Insert text with word wrapping
        text_length = page.insert_textbox(
            rect,
            text,
            fontsize=font_size,
            fontname=font_name,
            align=fitz.TEXT_ALIGN_CENTER if center else fitz.TEXT_ALIGN_LEFT,
        )

        # Estimate lines used (rough calculation)
        chars_per_line = content_width / (font_size * 0.5)
        estimated_lines = max(1, len(text) / chars_per_line)
        line_height = font_size * 1.2

        return y_position + (estimated_lines * line_height) + 5
