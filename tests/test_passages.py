"""Tests for cutting PDFs into passages and searching them."""

import pytest

from ai_writer.passages import MAX_WORDS, PassageIndex, cut_pdf
from ai_writer.zotero import Zotero
from tests.conftest import FakeEmbedder
from tests.fake_zotero import FakeZotero, filler, make_pdf

SECTIONS = [
    ("Abstract", filler("empathy", 160)),
    ("Introduction", filler("chatbot", 700)),
    ("Methods", filler("survey", 200)),
    ("Acknowledgements", filler("funding", 160)),
    ("References", filler("citation", 300)),
]


class CountingEmbedder(FakeEmbedder):
    def __init__(self, model_name="fake-embedder"):
        super().__init__(model_name)
        self.passages = 0

    def embed(self, texts, kind="passage"):
        self.passages += len(texts) if kind == "passage" else 0
        return super().embed(texts, kind)


@pytest.fixture
def library(tmp_path):
    fake = FakeZotero(tmp_path / "Zotero")
    fake.add_work("AAAA1111", "Empathy in chatbots", [("Ana", "Smith")], date="2020")
    make_pdf(fake.add_pdf("PDF00001", "AAAA1111", "smith.pdf"), SECTIONS)
    fake.add_work("BBBB2222", "Robots that navigate", [("Bo", "Lee")], date="2021")
    make_pdf(fake.add_pdf("PDF00002", "BBBB2222", "lee.pdf"),
             [("Abstract", filler("robot", 160)), ("Introduction", filler("navigation", 200)),
              ("Results", filler("lidar", 200))], outline=True)
    fake.add_work("CCCC3333", "No file here", [("Cy", "Diaz")], date="2022")
    fake.add_collection("COLL0001", "Empatía", ["AAAA1111"])
    return fake


def index_of(fake, tmp_path, embedder=None):
    return PassageIndex(Zotero(fake.root), tmp_path / "indice", embedder or FakeEmbedder())


@pytest.mark.parametrize("outline, source", [(False, "letra"), (True, "indice")])
def test_cut_follows_sections_and_pages(tmp_path, outline, source):
    cut = cut_pdf(make_pdf(tmp_path / "paper.pdf", SECTIONS, outline=outline))
    assert cut["secciones_por"] == source
    sections = list(dict.fromkeys(p["seccion"] for p in cut["pasajes"]))
    assert sections == ["Abstract", "Introduction", "Methods"]  # no acknowledgements, no references
    assert all(len(p["texto"].split()) <= MAX_WORDS for p in cut["pasajes"])
    intro = [p for p in cut["pasajes"] if p["seccion"] == "Introduction"]
    assert len(intro) >= 3 and all("chatbot" in p["texto"] for p in intro)
    assert intro[0]["paginas"][0] == 2 and intro[-1]["paginas"][1] == 4
    assert [p["paginas"] for p in cut["pasajes"] if p["seccion"] == "Methods"] == [[5, 5]]


def test_cut_without_headings_falls_back_to_size(tmp_path):
    import fitz

    doc = fitz.open()
    for _ in range(3):
        doc.new_page().insert_textbox(fitz.Rect(72, 72, 520, 780), filler("plain", 250), fontsize=10)
    doc.save(tmp_path / "plain.pdf")
    cut = cut_pdf(tmp_path / "plain.pdf")
    assert cut["secciones_por"] == "tamaño"
    assert {p["seccion"] for p in cut["pasajes"]} == {"Texto"} and len(cut["pasajes"]) >= 2


def test_update_is_incremental(library, tmp_path):
    embedder = CountingEmbedder()
    index = index_of(library, tmp_path, embedder)
    assert index.status() == {"obras": 3, "con_pdf": 2, "sin_pdf": 1, "indexadas": 0, "pendientes": 2,
                              "pasajes": 0, "sin_texto": 0}
    done = index.update()
    assert sorted(done["indexadas"]) == ["lee2021robots", "smith2020empathy"]
    embedded = embedder.passages
    assert embedded == index.status()["pasajes"] > 0

    assert index_of(library, tmp_path, embedder).update()["indexadas"] == []  # nothing changed
    make_pdf(library.root / "storage" / "PDF00002" / "lee.pdf",
             [("Abstract", filler("drone", 160)), ("Introduction", filler("flight", 200)),
              ("Results", filler("rotor", 200))])
    again = index_of(library, tmp_path, embedder)
    assert again.update()["indexadas"] == ["lee2021robots"]
    assert embedder.passages < 2 * embedded
    assert "drone" in again.passages_of("lee2021robots")[0]["texto"]

    other_model = index_of(library, tmp_path, CountingEmbedder("another-model"))
    assert len(other_model.pending()) == 2  # vectors of another model are not comparable


def test_pdf_without_text_is_reported(library, tmp_path):
    import fitz

    library.add_work("DDDD4444", "Scanned", [("Di", "Roy")], date="2019")
    blank = fitz.open()
    blank.new_page()
    blank.save(library.add_pdf("PDF00004", "DDDD4444", "scan.pdf"))
    library.add_work("EEEE5555", "Broken", [("Ed", "Poe")], date="2018")
    library.add_pdf("PDF00005", "EEEE5555", "broken.pdf", content=b"not a pdf")
    index = index_of(library, tmp_path)
    done = index.update()
    assert done["sin_texto"] == ["roy2019scanned"]
    assert [f["clave"] for f in done["fallidas"]] == ["poe2018broken"]
    assert len(done["indexadas"]) == 2 and index.search("empathy chatbot")


def test_search_scopes_and_caps_per_work(library, tmp_path):
    index = index_of(library, tmp_path)
    index.update()
    top = index.search("lidar outcomes of the robot", n=4)
    assert top[0]["clave"] == "lee2021robots" and top[0]["seccion"] == "Results"
    assert set(top[0]) == {
        "id", "clave", "titulo", "año", "seccion", "paginas", "texto", "relevancia",
        "archivo", "zotero_url",
    }
    assert top[0]["id"].startswith("lee2021robots#") and top[0]["paginas"] == "3"

    scope = Zotero(library.root).item_keys(["Empatía"])
    assert {r["clave"] for r in index.search("lidar robot", item_keys=scope)} == {"smith2020empathy"}
    assert len(index.search("study conditions", n=10, max_per_work=1)) == 2
    assert index.search("   ") == []


def test_words_rescue_what_meaning_misses(library, tmp_path):
    class Blind(FakeEmbedder):  # every text looks the same: only the words can tell
        def embed(self, texts, kind="passage"):
            import numpy as np
            return np.ones((len(texts), 4), dtype=np.float32)

    index = index_of(library, tmp_path, Blind())
    index.update()
    assert index.search("lidar", n=1)[0]["seccion"] == "Results"


def test_read_around_a_passage(library, tmp_path):
    index = index_of(library, tmp_path)
    index.update()
    passages = index.passages_of("smith2020empathy")
    intro = [p for p in passages if p["seccion"] == "Introduction"]
    middle = intro[1]["id"]
    assert [p["id"] for p in index.read(middle)] == [intro[0]["id"], middle, intro[2]["id"]]
    assert index.read(middle, "seccion") == intro
    assert index.read("smith2020empathy#999") == [] and index.read("nadie#1") == []
    assert [p["seccion"] for p in index.pages("smith2020empathy", 5, 5)] == ["Methods"]
    assert index.passages_of("diaz2022file") == []
