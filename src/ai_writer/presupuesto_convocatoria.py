"""Budget thresholds for the declared language of a call application."""

import re
import unicodedata
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, TypeAdapter

Amount = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]
_AMOUNT = TypeAdapter(Amount)
_DIRECT_COSTS = re.compile(r"\b(?:cost[eo]s directos|direct costs)\b")
_EUR = re.compile(r"(?<![\w.,])([0-9]+(?:[., ][0-9]+)*)\s*(?:€|euros?\b|eur\b)")
_MINIMUM = re.compile(r"\b(?:al menos|como mínimo|igual o superior a|at least)\s+$")
_LANGUAGES = {"es": "español", "en": "inglés", "fr": "francés", "pt": "portugués",
              "de": "alemán", "it": "italiano"}
_LANGUAGE_CODES = {name: code for code, name in _LANGUAGES.items()} | {
    "english": "en", "spanish": "es",
}
_REQUIRED_LANGUAGE = re.compile(
    r"\b(?:obligatori[oa]|debe(?:rá)?|must)\b[^;:.!?]{0,65}\b(?:en|in)\s+"
    r"(español|inglés|francés|portugués|alemán|italiano|english|spanish)\b"
)


class BudgetLanguage(BaseModel):
    desde_eur: Amount
    idioma: str = Field(pattern=r"^[a-z]{2,3}(?:-[a-zA-Z0-9]{2,8})*$")


def read_amount(value: str) -> Decimal:
    """Read an ungrouped euro amount from a tool argument or saved setting."""
    if not re.fullmatch(r"[0-9]{1,14}(?:[.,][0-9]{1,2})?", value.strip()):
        raise ValueError("Indica los costes directos en euros, sin separador de miles.")
    return _AMOUNT.validate_python(value.strip().replace(",", "."))


def quoted_budget_language(quote: str) -> tuple[Decimal | None, str | None]:
    """Read an explicit inclusive EUR threshold and language from the same clause."""
    text = " ".join(unicodedata.normalize("NFKC", quote).casefold().split())
    clauses = re.split(r"(?<=[.!?])\s+|;\s*", text)
    candidates = []
    for clause in clauses:
        euro = list(_EUR.finditer(clause))
        if not _DIRECT_COSTS.search(clause) or len(euro) != 1:
            continue
        match, = euro
        if not _MINIMUM.search(clause[:match.start()]):
            continue
        number = match[1]
        if re.fullmatch(r"[0-9]{1,3}(?:[. ][0-9]{3})+(?:,[0-9]{1,2})?", number):
            number = number.replace(".", "").replace(" ", "")
        try:
            threshold = read_amount(number)
        except ValueError:
            continue
        required = {_LANGUAGE_CODES[name] for name in _REQUIRED_LANGUAGE.findall(clause)}
        candidates.append((threshold, next(iter(required)) if len(required) == 1 else None))
    return candidates[0] if len(candidates) == 1 else (None, None)


def language_name(code: str) -> str:
    return _LANGUAGES.get(code.split("-", 1)[0].lower(), code)


def budget_language_status(
    rule: BudgetLanguage, amount: Decimal | None, declared: str, approved: bool,
) -> dict:
    status = "ficha_pendiente"
    question = None
    if approved:
        if amount is None:
            status = "costes_pendientes"
            question = "¿Qué importe en euros se solicita en costes directos?"
        elif amount < rule.desde_eur:
            status = "no_aplica"
        else:
            expected = rule.idioma.lower()
            language = declared.strip().lower().replace("_", "-")
            matches = language == expected or language.startswith(expected + "-")
            status = "ok" if matches else "idioma_distinto"
    return {
        "estado": status,
        "pregunta": question,
        "importe_eur": f"{amount:.2f}" if amount is not None else None,
        "desde_eur": f"{rule.desde_eur:.2f}",
        "idioma_requerido": rule.idioma,
        "idioma_declarado": declared,
    }
