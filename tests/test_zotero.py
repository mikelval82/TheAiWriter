"""Tests for the read-only view of a local Zotero library."""

import pytest

from ai_writer.citations import find_citations, make_key
from ai_writer.zotero import ZOTERO_ENV, Zotero, ZoteroError, assign_keys, data_dir
from tests.fake_zotero import FakeZotero


@pytest.fixture
def fake(tmp_path):
    fake = FakeZotero(tmp_path / "Zotero")
    fake.add_work("AAAA1111", "Empathy in conversational agents",
                  [("Ana", "Smith"), ("Luis", "van der Berg")],
                  date="2020-03-00 03/2020", DOI="10.1/abc", publicationTitle="Journal of Agents")
    fake.add_pdf("PDF00001", "AAAA1111", "Smith 2020.pdf")
    fake.add_work("BBBB2222", "A survey of affective computing", [("", "Consortium")],
                  kind="preprint", date="2023", repository="arXiv", citationKey="consortium_survey_2023")
    fake.add_work("CCCC3333", "Without a file", [("Eva", "Ruiz", "editor")],
                  extra="tex.ids= x\nCitation Key: ruizSinArchivo")
    fake.add_collection("COLL0001", "Empatía", ["AAAA1111"])
    fake.add_collection("COLL0002", "Revisiones", ["BBBB2222"], parent="COLL0001")
    fake.add_collection("COLL0003", "Otra", ["CCCC3333"])
    return fake


def test_works_carry_metadata_and_pdfs(fake):
    zotero = Zotero(fake.root)
    work = zotero.work("AAAA1111")
    assert work.title == "Empathy in conversational agents"
    assert work.authors == ("Smith, Ana", "van der Berg, Luis")
    assert (work.year, work.doi, work.venue) == (2020, "10.1/abc", "Journal of Agents")
    assert [p.name for p in work.pdfs] == ["Smith 2020.pdf"]
    assert work.pdfs[0].parent == fake.root / "storage" / "PDF00001"

    preprint = zotero.work("BBBB2222")
    assert (preprint.kind, preprint.authors, preprint.venue) == ("preprint", ("Consortium",), "arXiv")
    assert preprint.zotero_cite_key == "consortium_survey_2023"
    assert preprint.pdfs == ()

    edited = zotero.work("CCCC3333")
    assert edited.authors == ("Ruiz, Eva",)  # editors stand in when there are no authors
    assert edited.zotero_cite_key == "ruizSinArchivo"


def test_attachments_and_notes_are_not_works_but_loose_pdfs_are(fake):
    fake.add_pdf("PDF00009", None, "Loose paper.pdf")
    zotero = Zotero(fake.root)
    assert {w.item_key for w in zotero.works()} == {"AAAA1111", "BBBB2222", "CCCC3333", "PDF00009"}
    assert zotero.work("PDF00009").title == "Loose paper"


def test_linked_and_missing_pdfs(fake, tmp_path):
    linked = tmp_path / "elsewhere" / "linked.pdf"
    fake.add_pdf("PDF00002", "BBBB2222", linked=linked)
    fake.add_pdf("PDF00003", "CCCC3333", "not downloaded.pdf", on_disk=False)
    zotero = Zotero(fake.root)
    assert zotero.work("BBBB2222").pdfs == (linked,)
    assert zotero.work("CCCC3333").pdfs == ()


def test_deleted_items_and_collections_are_ignored(fake):
    fake.delete_item("AAAA1111")
    fake.delete_collection("COLL0003")
    zotero = Zotero(fake.root)
    assert zotero.work("AAAA1111") is None
    assert [c.path for c in zotero.collections()] == ["Empatía", "Empatía / Revisiones"]
    assert zotero.collection("Empatía").item_keys == ()


def test_collections_include_their_subcollections(fake):
    zotero = Zotero(fake.root)
    assert zotero.item_keys(["empatía"]) == {"AAAA1111", "BBBB2222"}
    assert zotero.item_keys(["Empatía / Revisiones"]) == {"BBBB2222"}
    assert zotero.item_keys(["COLL0003", "Revisiones"]) == {"BBBB2222", "CCCC3333"}
    assert len(zotero.item_keys()) == 3
    assert [w.item_key for w in zotero.works(["Empatía"])] == ["AAAA1111", "BBBB2222"]


def test_unknown_and_ambiguous_collections(fake):
    fake.add_collection("COLL0004", "Revisiones", parent="COLL0003")
    zotero = Zotero(fake.root)
    with pytest.raises(ZoteroError, match="No hay ninguna"):
        zotero.collection("Nada")
    with pytest.raises(ZoteroError, match="ruta completa"):
        zotero.collection("Revisiones")
    assert zotero.collection("Otra / Revisiones").key == "COLL0004"


def test_reads_changes_still_in_the_wal_without_touching_the_folder(tmp_path):
    fake = FakeZotero(tmp_path / "Zotero")
    fake.db.execute("PRAGMA journal_mode = WAL")
    fake.db.execute("PRAGMA wal_autocheckpoint = 0")
    fake.add_work("AAAA1111", "Only in the WAL")  # the connection stays open, like Zotero's
    before = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in fake.root.iterdir())

    assert Zotero(fake.root).work("AAAA1111").title == "Only in the WAL"
    assert sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in fake.root.iterdir()) == before


def test_missing_library(tmp_path, monkeypatch):
    with pytest.raises(ZoteroError, match="No encuentro"):
        Zotero(tmp_path / "nothing")
    monkeypatch.setenv(ZOTERO_ENV, str(tmp_path / "mine"))
    assert data_dir() == tmp_path / "mine"


def test_keys_are_stable_once_assigned(fake):
    works = Zotero(fake.root).works()
    keys = assign_keys(works, {})
    assert keys == {"AAAA1111": "smith2020empathy", "BBBB2222": "consortium_survey_2023",
                    "CCCC3333": "ruizSinArchivo"}

    fake.add_work("DDDD4444", "Empathy revisited", [("Bob", "Smith")], date="2020")
    fake.add_work("EEEE5555", "Later", [("Zoe", "Lee")], citationKey="smith2020empathy")
    again = assign_keys(Zotero(fake.root).works(), {"AAAA1111": "smith2020empathy", "BBBB2222": "antigua"})
    assert again["AAAA1111"] == "smith2020empathy"
    assert again["BBBB2222"] == "antigua"  # a Zotero key that appears later does not rename the work
    assert again["DDDD4444"] == "smith2020empathyb"
    assert again["EEEE5555"] == "leesflater"  # its Zotero key was already taken


def test_keys_are_bibtex_style_and_unique():
    taken = set()
    first = make_key(["Ana Smith"], 2020, "The Emotion Models", taken)
    taken.add(first)

    assert first == "smith2020emotion"
    assert make_key(["Smith, Ana"], 2020, "Emotion again", taken) == "smith2020emotionb"
    assert make_key([], None, "Á la carte", set()) == "anonimosfcarte"


def test_find_citations_accepts_pandoc_syntax_and_flags_the_old_format():
    keys, malformed, pending = find_citations(
        "A [@smith2020emotion]. B [@a2020x; @b2021y, p. 4]. C [@Brown et al., 2020]. D [@?]."
    )

    assert keys == ["smith2020emotion", "a2020x", "b2021y"]
    assert malformed == ["[@Brown et al., 2020]"]
    assert pending == 1


def test_documents_dir_uses_the_localized_documents_folder(tmp_path, monkeypatch):
    from ai_writer.library import documents_dir

    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    (tmp_path / "user-dirs.dirs").write_text(
        'XDG_DOCUMENTS_DIR="$HOME/Documentos"\n', encoding="utf-8"
    )
    assert documents_dir() == tmp_path / "Documentos"
