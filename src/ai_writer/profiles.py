"""Document profiles: the sections a document has and which topics feed each one.

A section's ``topics`` says which topics of the document's papers its planning
ideas come from, with topics ordered from largest to smallest:

- ``principales``: the largest ones (overview, conclusions)
- ``todos``: every topic (state of the art, discussion)
- ``minoritarios``: the smaller half (gaps, open problems)
- ``variados``: every other topic (challenges, contrasts)

``target_words`` is the length the whole document aims at; each paragraph gets
its share of it (see ``Profile.paragraph_words``).
"""

from dataclasses import dataclass
from typing import Literal

TopicChoice = Literal["principales", "todos", "minoritarios", "variados"]
PARAGRAPH_WORDS = (110, 230)  # a paragraph's length is kept between these, whatever the target


@dataclass(frozen=True)
class SectionSpec:
    name: str
    purpose: str
    min_paragraphs: int
    max_paragraphs: int
    topics: TopicChoice = "principales"

    def as_planner_tuple(self) -> tuple[str, str, int, int]:
        return (self.name, self.purpose, self.min_paragraphs, self.max_paragraphs)


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    sections: tuple[SectionSpec, ...]
    target_words: int

    def section(self, name: str) -> SectionSpec | None:
        return next((s for s in self.sections if s.name == name), None)

    def paragraph_words(self, n_paragraphs: int) -> tuple[int, int]:
        """The word range for each of ``n_paragraphs`` paragraphs to add up to ``target_words``."""
        words = min(PARAGRAPH_WORDS[1], max(PARAGRAPH_WORDS[0], self.target_words // max(1, n_paragraphs)))
        return round(words * 0.8), round(words * 1.2)

    def topic_ids(self, section: SectionSpec, ordered_topic_ids: list[int]) -> list[int]:
        """The topics feeding ``section``, given the topic ids from largest to smallest."""
        n = len(ordered_topic_ids)
        if section.topics == "todos":
            return ordered_topic_ids
        if section.topics == "minoritarios":
            return ordered_topic_ids[n // 2:]
        if section.topics == "variados":
            return ordered_topic_ids[::2]
        return ordered_topic_ids[: max(3, n // 2)]


PROFILES = {
    "perspectiva": Profile(
        name="perspectiva",
        description="Paper de perspectiva: propone una visión propia apoyada en la literatura",
        target_words=5000,
        sections=(
            SectionSpec("Introducción", "Presentar el tema, su relevancia y la tesis central del paper", 2, 3),
            SectionSpec("Estado Actual del Arte", "Revisar los avances recientes y el conocimiento establecido", 3, 5, "todos"),
            SectionSpec("Identificación del Problema o Brecha", "Identificar limitaciones, contradicciones o áreas no exploradas", 2, 3, "minoritarios"),
            SectionSpec("La Nueva Perspectiva", "Proponer la visión o enfoque novedoso del autor", 3, 4),
            SectionSpec("Discusión", "Analizar implicaciones, comparar con enfoques existentes", 3, 5, "todos"),
            SectionSpec("Implicaciones Futuras", "Proyectar el impacto potencial y direcciones de investigación", 2, 3),
            SectionSpec("Desafíos y Limitaciones", "Reconocer obstáculos y limitaciones de la perspectiva", 2, 3, "variados"),
            SectionSpec("Conclusiones", "Sintetizar los puntos clave y el mensaje final", 1, 2),
        ),
    ),
    "revision": Profile(
        name="revision",
        description="Revisión narrativa: sintetiza y compara lo que dice la literatura sobre un tema",
        target_words=6000,
        sections=(
            SectionSpec("Introducción", "Presentar el tema, por qué importa y la pregunta que guía la revisión", 2, 3),
            SectionSpec("Alcance y Fuentes", "Describir qué trabajos se revisan, de qué tipo son y qué periodo cubren", 1, 2, "todos"),
            SectionSpec("Síntesis Temática", "Organizar los hallazgos por temas, con lo que cada grupo de trabajos aporta", 4, 6, "todos"),
            SectionSpec("Convergencias y Tensiones", "Contrastar resultados y enfoques: dónde coinciden y dónde se contradicen", 2, 4, "variados"),
            SectionSpec("Lagunas y Líneas Abiertas", "Señalar lo que la literatura no resuelve y qué habría que investigar", 2, 3, "minoritarios"),
            SectionSpec("Conclusiones", "Resumir el estado de la cuestión y su utilidad práctica", 1, 2),
        ),
    ),
    "ensayo": Profile(
        name="ensayo",
        description="Ensayo breve: un argumento central, sus apoyos y sus objeciones",
        target_words=3000,
        sections=(
            SectionSpec("Introducción", "Plantear la pregunta y la tesis", 1, 2),
            SectionSpec("Argumento", "Desarrollar la tesis con la evidencia más sólida", 2, 4, "todos"),
            SectionSpec("Objeciones y Respuestas", "Presentar las objeciones más serias y responderlas", 2, 3, "variados"),
            SectionSpec("Conclusión", "Cerrar con lo que se sigue de la tesis", 1, 2),
        ),
    ),
}


def profile_for(name: str | None, kind: str = "perspectiva") -> Profile:
    """The named profile, or the default one for the document kind.

    Raises:
        ValueError: If the profile does not exist.
    """
    name = name or ("perspectiva" if kind == "perspectiva" else kind)
    if name not in PROFILES:
        raise ValueError(f"No existe el perfil «{name}». Disponibles: {', '.join(PROFILES)}.")
    return PROFILES[name]
