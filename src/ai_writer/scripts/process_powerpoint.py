"""
PowerPoint to Text Processor using OpenAI Vision.

This script extracts slides from a PowerPoint presentation, converts them to images,
uses GPT-4o's vision capabilities to interpret each slide, and generates a coherent
text document from all slide descriptions.
"""

import argparse
import base64
import io
import sys
from pathlib import Path

from openai import OpenAI
from pptx import Presentation
from pptx.util import Inches
from PIL import Image
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.settings import settings


console = Console()


class PowerPointProcessor:
    """Processes PowerPoint presentations using OpenAI Vision."""

    def __init__(
        self,
        api_key: str | None = None,
        vision_model: str = "gpt-4o",
        final_model: str | None = None,
        output_dir: Path | None = None,
    ):
        """
        Initialize the PowerPoint processor.

        Args:
            api_key: OpenAI API key. Defaults to settings.
            vision_model: Vision model for slide analysis. Defaults to gpt-4o.
            final_model: Model for final document generation. Defaults to settings.ai.default_model.
            output_dir: Output directory for results.
        """
        self.api_key = api_key or settings.ai.openai_api_key
        self.vision_model = vision_model
        self.final_model = final_model or settings.ai.default_model
        self.output_dir = output_dir or settings.paths.output_dir / "powerpoint"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = OpenAI(api_key=self.api_key)

    def extract_slides_as_images(self, pptx_path: Path) -> list[tuple[int, Image.Image]]:
        """
        Extract slides from PowerPoint as images.

        Note: python-pptx cannot directly render slides as images.
        We use an alternative approach: extract embedded images and text,
        or use pdf conversion with external tools.

        For full slide rendering, we'll use a workaround with slide thumbnails
        or export functionality.

        Args:
            pptx_path: Path to the PowerPoint file.

        Returns:
            List of tuples (slide_number, image).
        """
        console.print(f"[blue]📂 Loading presentation: {pptx_path.name}[/blue]")
        
        prs = Presentation(pptx_path)
        slides_data = []
        
        for idx, slide in enumerate(prs.slides, start=1):
            # Extract slide content as structured data
            slide_info = self._extract_slide_content(slide, idx)
            slides_data.append((idx, slide_info))
        
        return slides_data, prs

    def _extract_slide_content(self, slide, slide_num: int) -> dict:
        """
        Extract content from a slide including text and images.

        Args:
            slide: PowerPoint slide object.
            slide_num: Slide number.

        Returns:
            Dictionary with slide content.
        """
        content = {
            "slide_number": slide_num,
            "texts": [],
            "images": [],
            "notes": "",
        }

        # Extract text from shapes
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    text = paragraph.text.strip()
                    if text:
                        content["texts"].append(text)

            # Extract images
            if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
                try:
                    image_bytes = shape.image.blob
                    image = Image.open(io.BytesIO(image_bytes))
                    content["images"].append(image)
                except Exception as e:
                    console.print(f"[yellow]⚠️ Could not extract image: {e}[/yellow]")

        # Extract speaker notes
        if slide.has_notes_slide:
            notes_frame = slide.notes_slide.notes_text_frame
            if notes_frame:
                content["notes"] = notes_frame.text.strip()

        return content

    def slide_to_image(self, pptx_path: Path, slide_num: int) -> Image.Image | None:
        """
        Convert a specific slide to an image using pdf export.

        This requires external tools like LibreOffice or unoconv.
        As an alternative, we can use the comtypes library on Windows.

        Args:
            pptx_path: Path to PowerPoint file.
            slide_num: Slide number to convert.

        Returns:
            PIL Image of the slide or None.
        """
        try:
            import comtypes.client
            import pythoncom
            
            pythoncom.CoInitialize()
            
            powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
            powerpoint.Visible = 1
            
            presentation = powerpoint.Presentations.Open(str(pptx_path.absolute()))
            
            # Export slide as image
            temp_dir = self.output_dir / "temp_slides"
            temp_dir.mkdir(exist_ok=True)
            
            slide = presentation.Slides(slide_num)
            image_path = temp_dir / f"slide_{slide_num}.png"
            slide.Export(str(image_path), "PNG", 1920, 1080)
            
            presentation.Close()
            powerpoint.Quit()
            
            pythoncom.CoUninitialize()
            
            if image_path.exists():
                return Image.open(image_path)
            
        except ImportError:
            console.print("[yellow]⚠️ comtypes not available, using text extraction mode[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️ PowerPoint COM not available: {e}[/yellow]")
        
        return None

    def export_slides_as_images_batch(self, pptx_path: Path) -> list[Path]:
        """
        Export all slides as images using PowerPoint COM automation.

        Args:
            pptx_path: Path to PowerPoint file.

        Returns:
            List of paths to exported images.
        """
        image_paths = []
        
        try:
            import comtypes.client
            import pythoncom
            
            pythoncom.CoInitialize()
            
            console.print("[blue]🖥️ Using PowerPoint COM automation...[/blue]")
            
            powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
            powerpoint.Visible = 1
            
            presentation = powerpoint.Presentations.Open(str(pptx_path.absolute()))
            
            temp_dir = self.output_dir / "temp_slides"
            temp_dir.mkdir(exist_ok=True)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Exporting slides...", 
                    total=presentation.Slides.Count
                )
                
                for i in range(1, presentation.Slides.Count + 1):
                    slide = presentation.Slides(i)
                    image_path = temp_dir / f"slide_{i:03d}.png"
                    slide.Export(str(image_path), "PNG", 1920, 1080)
                    image_paths.append(image_path)
                    progress.update(task, advance=1)
            
            presentation.Close()
            powerpoint.Quit()
            pythoncom.CoUninitialize()
            
            console.print(f"[green]✅ Exported {len(image_paths)} slides as images[/green]")
            
        except ImportError:
            console.print("[yellow]⚠️ comtypes not installed. Install with: pip install comtypes[/yellow]")
            console.print("[yellow]   Falling back to text extraction mode...[/yellow]")
        except OSError as e:
            console.print(f"[yellow]⚠️ Microsoft PowerPoint not installed or not accessible[/yellow]")
            console.print(f"[dim]   Error: {e}[/dim]")
            console.print("[yellow]   Falling back to text extraction mode...[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ PowerPoint automation failed: {e}[/red]")
            console.print("[yellow]   Falling back to text extraction mode...[/yellow]")
        
        return image_paths

    def encode_image_to_base64(self, image: Image.Image | Path) -> str:
        """
        Encode an image to base64 for OpenAI API.

        Args:
            image: PIL Image or path to image file.

        Returns:
            Base64 encoded string.
        """
        if isinstance(image, Path):
            with open(image, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        else:
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def describe_slide_image(
        self, 
        image: Image.Image | Path, 
        slide_num: int,
        context: str = "",
    ) -> str:
        """
        Use OpenAI Vision to describe a slide image.

        Args:
            image: PIL Image or path to image.
            slide_num: Slide number for context.
            context: Additional context from previous slides.

        Returns:
            Text description of the slide.
        """
        base64_image = self.encode_image_to_base64(image)

        system_prompt = """Eres un experto en analizar presentaciones. Tu tarea es:
1. Describir el contenido visual de la diapositiva de forma detallada
2. Extraer el texto visible
3. Interpretar gráficos, diagramas o imágenes
4. Identificar los puntos clave del mensaje

Responde en español, de forma clara y estructurada."""

        user_prompt = f"""Analiza la diapositiva #{slide_num} de esta presentación.

{f"Contexto de diapositivas anteriores: {context}" if context else ""}

Proporciona:
1. **Título/Encabezado**: El título de la diapositiva si lo hay
2. **Contenido principal**: Descripción del contenido
3. **Elementos visuales**: Descripción de gráficos, imágenes, diagramas
4. **Puntos clave**: Los mensajes principales de esta diapositiva"""

        response = self.client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
            max_tokens=2000,
            temperature=0.3,
        )

        return response.choices[0].message.content

    def describe_slide_from_content(
        self, 
        content: dict, 
        context: str = "",
    ) -> str:
        """
        Describe a slide from extracted text and images.

        Args:
            content: Dictionary with slide content.
            context: Additional context from previous slides.

        Returns:
            Text description of the slide.
        """
        slide_num = content["slide_number"]
        texts = content["texts"]
        images = content["images"]
        notes = content["notes"]

        # Build content description
        content_parts = []
        
        if texts:
            content_parts.append(f"**Textos en la diapositiva:**\n" + "\n".join(f"- {t}" for t in texts))
        
        if notes:
            content_parts.append(f"**Notas del presentador:**\n{notes}")

        content_text = "\n\n".join(content_parts) if content_parts else "Sin texto extraíble"

        # If there are images, analyze them
        image_descriptions = []
        for i, img in enumerate(images, 1):
            try:
                base64_image = self.encode_image_to_base64(img)
                response = self.client.chat.completions.create(
                    model=self.vision_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Describe brevemente esta imagen de la diapositiva {slide_num}:",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}",
                                        "detail": "low",
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=500,
                    temperature=0.3,
                )
                image_descriptions.append(f"Imagen {i}: {response.choices[0].message.content}")
            except Exception as e:
                console.print(f"[yellow]⚠️ Error analyzing image: {e}[/yellow]")

        if image_descriptions:
            content_text += "\n\n**Imágenes:**\n" + "\n".join(image_descriptions)

        # Now synthesize with GPT
        system_prompt = """Eres un experto en sintetizar información de presentaciones.
A partir del contenido extraído de una diapositiva, genera una descripción
coherente y bien estructurada en español."""

        user_prompt = f"""Diapositiva #{slide_num}

{content_text}

{f"Contexto previo: {context}" if context else ""}

Genera una descripción coherente de esta diapositiva."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Use faster model for text synthesis
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1000,
            temperature=0.3,
        )

        return response.choices[0].message.content

    def generate_coherent_document(self, slide_descriptions: list[str], title: str = "") -> str:
        """
        Generate a coherent document from all slide descriptions.

        Args:
            slide_descriptions: List of descriptions for each slide.
            title: Optional presentation title.

        Returns:
            Coherent text document.
        """
        console.print("[blue]📝 Generating coherent document...[/blue]")

        all_content = "\n\n---\n\n".join(
            f"**Diapositiva {i+1}:**\n{desc}" 
            for i, desc in enumerate(slide_descriptions)
        )

        system_prompt = """Eres un experto redactor técnico. Tu tarea es transformar
las descripciones individuales de diapositivas en un documento coherente y fluido.

Debes:
1. Mantener toda la información importante
2. Crear transiciones naturales entre secciones
3. Organizar el contenido de forma lógica
4. Usar un tono profesional y claro
5. Incluir una introducción y conclusión si es apropiado

Responde en español."""

        user_prompt = f"""{"Título de la presentación: " + title if title else ""}

Contenido de las diapositivas:

{all_content}

Genera un documento coherente y bien estructurado basándote en este contenido."""

        console.print(f"[blue]   Using model: {self.final_model}[/blue]")
        
        # GPT-5.x models use max_completion_tokens, older models use max_tokens
        token_param = "max_completion_tokens" if "gpt-5" in self.final_model else "max_tokens"
        
        response = self.client.chat.completions.create(
            model=self.final_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **{token_param: 16000},
            temperature=0.4,
        )

        return response.choices[0].message.content

    def process_presentation(
        self, 
        pptx_path: Path, 
        use_com: bool = True,
        save_intermediate: bool = True,
    ) -> tuple[list[str], str]:
        """
        Process a complete PowerPoint presentation.

        Args:
            pptx_path: Path to the PowerPoint file.
            use_com: Try to use PowerPoint COM for image export.
            save_intermediate: Save intermediate slide descriptions.

        Returns:
            Tuple of (slide_descriptions, final_document).
        """
        pptx_path = Path(pptx_path)
        
        if not pptx_path.exists():
            raise FileNotFoundError(f"PowerPoint file not found: {pptx_path}")

        console.print(f"\n[bold green]🚀 Processing: {pptx_path.name}[/bold green]\n")

        slide_descriptions = []
        image_paths = []
        
        # Try COM automation first for best quality
        if use_com:
            image_paths = self.export_slides_as_images_batch(pptx_path)

        if image_paths:
            # Process from exported images
            console.print("\n[blue]🔍 Analyzing slides with vision...[/blue]\n")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Analyzing slides...", 
                    total=len(image_paths)
                )
                
                context = ""
                for i, img_path in enumerate(image_paths, 1):
                    description = self.describe_slide_image(img_path, i, context)
                    slide_descriptions.append(description)
                    context = description[:500]  # Use last slide as context
                    progress.update(task, advance=1)
                    
                    console.print(f"[dim]  ✓ Slide {i} analyzed[/dim]")
        else:
            # Fallback to text extraction
            console.print("\n[blue]📄 Extracting slide content...[/blue]\n")
            
            slides_data, prs = self.extract_slides_as_images(pptx_path)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Processing slides...", 
                    total=len(slides_data)
                )
                
                context = ""
                for slide_num, content in slides_data:
                    description = self.describe_slide_from_content(content, context)
                    slide_descriptions.append(description)
                    context = description[:500]
                    progress.update(task, advance=1)
                    
                    console.print(f"[dim]  ✓ Slide {slide_num} processed[/dim]")

        # Save intermediate results
        if save_intermediate:
            intermediate_path = self.output_dir / f"{pptx_path.stem}_slides.md"
            with open(intermediate_path, "w", encoding="utf-8") as f:
                f.write(f"# Análisis de Diapositivas: {pptx_path.stem}\n\n")
                for i, desc in enumerate(slide_descriptions, 1):
                    f.write(f"## Diapositiva {i}\n\n{desc}\n\n---\n\n")
            console.print(f"[dim]💾 Saved intermediate: {intermediate_path}[/dim]")

        # Generate coherent document
        final_document = self.generate_coherent_document(
            slide_descriptions, 
            title=pptx_path.stem
        )

        # Save final document
        final_path = self.output_dir / f"{pptx_path.stem}_document.md"
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(f"# {pptx_path.stem}\n\n")
            f.write(final_document)
        
        console.print(f"\n[bold green]✅ Complete! Final document saved to:[/bold green]")
        console.print(f"   [link]{final_path}[/link]\n")

        return slide_descriptions, final_document


def main():
    """Main entry point for PowerPoint processing."""
    parser = argparse.ArgumentParser(
        description="Process PowerPoint presentations with OpenAI Vision"
    )
    parser.add_argument(
        "pptx_path",
        type=str,
        help="Path to the PowerPoint file (.pptx)",
    )
    parser.add_argument(
        "--vision-model",
        type=str,
        default="gpt-4o",
        help="OpenAI vision model for slide analysis (default: gpt-4o)",
    )
    parser.add_argument(
        "--final-model",
        type=str,
        default=None,
        help=f"Model for final document generation (default: {settings.ai.default_model})",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results",
    )
    parser.add_argument(
        "--no-com",
        action="store_true",
        help="Skip COM automation (use text extraction only)",
    )
    parser.add_argument(
        "--no-intermediate",
        action="store_true",
        help="Don't save intermediate slide descriptions",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None
    
    console.print(f"\n[bold]📊 PowerPoint Processor[/bold]")
    console.print(f"   Vision model: [cyan]{args.vision_model}[/cyan]")
    console.print(f"   Final model:  [cyan]{args.final_model or settings.ai.default_model}[/cyan]\n")
    
    processor = PowerPointProcessor(
        vision_model=args.vision_model,
        final_model=args.final_model,
        output_dir=output_dir,
    )

    try:
        slides, document = processor.process_presentation(
            Path(args.pptx_path),
            use_com=not args.no_com,
            save_intermediate=not args.no_intermediate,
        )
        console.print(f"[green]Processed {len(slides)} slides successfully![/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
