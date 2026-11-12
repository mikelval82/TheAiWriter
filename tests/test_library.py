"""Tests for the library folder, its collections and document projects.

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
"""

import json

import pytest
from typer.testing import CliRunner

from ai_writer.library import (
    LIBRARY_ENV,
    Library,
    LibraryError,
    Project,
    default_library_dir,
    documents_dir,
)
from ai_writer.main import app
from config.settings import settings
from tests.conftest import PAPERS

runner = CliRunner()


@pytest.fixture
def processed(tmp_path):
    """A data/processed folder with one paper folder per synthetic paper."""
    root = tmp_path / "processed"
    for paper in PAPERS:
        folder = root / "papers" / paper["paper_id"]
        folder.mkdir(parents=True)
        metadata = {
            "paper_id": paper["paper_id"],
            "title": paper["paper_title"],
            "authors": paper["authors"],
            "year": paper["year"],
            "source_file": f"/somewhere/{paper['word']}.pdf",
        }
        (folder / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        (folder / "ideas.jsonl").write_text('{"idea": "a"}\n{"idea": "b"}\n', encoding="utf-8")
    (root / "indices").mkdir()
    (root / "indices" / "all_ideas.jsonl").write_text('{"idea": "a"}\n', encoding="utf-8")
    (root / "embeddings").mkdir()
    (root / "embeddings" / "ideas_index.npz").write_bytes(b"vectors")
    (root / "embeddings" / "ideas_metadata.json").write_text("{}", encoding="utf-8")
    (root / "embeddings" / "previous_old-model").mkdir()
    # Like the real corpus: the status file misses a paper.
    (root / "processing_status.json").write_text('{"processed": {}}', encoding="utf-8")
    return root


@pytest.fixture
def library(tmp_path, processed):
    library = Library(tmp_path / "biblioteca")
    library.migrate_from(processed)
    return library


def test_migration_copies_papers_indices_and_vectors_but_not_old_models(library):
    assert [p.id for p in library.papers()] == [
        "paper-emotion",
        "paper-navigation",
        "paper-speech",
    ]
    assert (library.indices_dir / "all_ideas.jsonl").exists()
    assert (library.embeddings_dir / "ideas_index.npz").read_bytes() == b"vectors"
    assert not (library.embeddings_dir / "previous_old-model").exists()
    assert library.papers()[0].ideas == 2


def test_migration_refuses_to_overwrite_a_library_with_papers(library, processed):
    with pytest.raises(LibraryError, match="ya tiene papers"):
        library.migrate_from(processed)


def test_activate_points_the_pipeline_paths_at_the_library(library, monkeypatch):
    for name in ("references_pdf_dir", "processed_dir", "indices_dir", "embeddings_dir"):
        monkeypatch.setattr(settings.paths, name, getattr(settings.paths, name))

    library.activate()

    assert settings.paths.embeddings_dir == library.embeddings_dir
    assert settings.paths.indices_dir == library.root / "procesado" / "indices"


def test_find_papers_by_title_fragment_file_or_id(library):
    found = library.find_papers(["crowded", "speech.pdf", "paper-emotion"])

    assert [p.id for p in found] == ["paper-navigation", "paper-speech", "paper-emotion"]


def test_find_papers_rejects_unknown_and_ambiguous_queries(library):
    with pytest.raises(LibraryError, match="Ningún paper"):
        library.find_papers(["quantum"])
    with pytest.raises(LibraryError, match="varios papers"):
        library.find_papers(["s"])


def test_collections_round_trip_and_resolve_to_paper_ids(library):
    library.save_collection("Robots", library.find_papers(["emotion", "crowded"]))

    assert library.collections() == {"Robots": ["paper-emotion", "paper-navigation"]}
    assert "titulo: Emotion Models for Social Robots" in library.collections_file.read_text(
        encoding="utf-8"
    )
    assert library.paper_ids(["Robots"]) == {"paper-emotion", "paper-navigation"}
    assert library.paper_ids() == {"paper-emotion", "paper-navigation", "paper-speech"}

    library.delete_collection("Robots")
    assert library.collections() == {}


def test_unknown_collection_names_the_available_ones(library):
    library.save_collection("Robots", library.find_papers(["emotion"]))

    with pytest.raises(LibraryError, match="Disponibles: Robots"):
        library.paper_ids(["Voz"])


def test_new_document_uses_a_collection_of_its_library(library, tmp_path):
    library.save_collection("Robots", library.find_papers(["emotion", "crowded"]))
    folder = tmp_path / "mi-paper"

    Project.create(
        folder, tipo="perspectiva", titulo="Robots sociales", colecciones=["Robots"],
        biblioteca=library.root,
    )

    project = Project.load(folder)
    assert project.paper_ids() == {"paper-emotion", "paper-navigation"}
    assert project.idioma == "es"
    for sub in ("materiales", "borrador", "revision", "exportacion"):
        assert (folder / sub).is_dir()


def test_new_document_refuses_unknown_collections_and_existing_projects(library, tmp_path):
    folder = tmp_path / "mi-paper"
    with pytest.raises(LibraryError, match="No existen las colecciones"):
        Project.create(folder, tipo="perspectiva", titulo="T", colecciones=["Voz"],
                       biblioteca=library.root)
    assert not (folder / "proyecto.yaml").exists()

    Project.create(folder, tipo="perspectiva", titulo="T", biblioteca=library.root)
    with pytest.raises(LibraryError, match="ya tiene"):
        Project.create(folder, tipo="perspectiva", titulo="T", biblioteca=library.root)


def test_default_library_lives_in_the_localized_documents_folder(tmp_path, monkeypatch):
    monkeypatch.delenv(LIBRARY_ENV, raising=False)
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "user-dirs.dirs").write_text(
        'XDG_DOCUMENTS_DIR="$HOME/Documentos"\n', encoding="utf-8"
    )

    assert documents_dir() == tmp_path / "Documentos"
    assert default_library_dir() == tmp_path / "Documentos" / "TheAIWriter" / "biblioteca"

    monkeypatch.setenv(LIBRARY_ENV, str(tmp_path / "otra"))
    assert default_library_dir() == tmp_path / "otra"


def test_cli_migrates_and_manages_collections(tmp_path, processed, workspace):
    target = tmp_path / "cli-biblioteca"

    result = runner.invoke(app, ["biblioteca", "migrar", "--ruta", str(target),
                                 "--desde", str(processed)])
    assert result.exit_code == 0, result.output
    assert "3 papers" in result.output

    result = runner.invoke(app, ["biblioteca", "coleccion", "Robots", "emotion", "crowded",
                                 "--ruta", str(target)])
    assert result.exit_code == 0, result.output
    assert Library(target).collections() == {"Robots": ["paper-emotion", "paper-navigation"]}

    result = runner.invoke(app, ["biblioteca", "coleccion", "Voz", "quantum",
                                 "--ruta", str(target)])
    assert result.exit_code == 1
    assert "Ningún paper" in result.output


def test_add_pdfs_copies_files_and_folders_once(library, tmp_path):
    source = tmp_path / "descargas"
    source.mkdir()
    (source / "a.pdf").write_bytes(b"%PDF")
    (source / "b.pdf").write_bytes(b"%PDF")

    assert [p.name for p in library.add_pdfs([source])] == ["a.pdf", "b.pdf"]
    assert library.add_pdfs([source / "a.pdf"]) == []
    assert [p.name for p in library.pending_pdfs()] == ["a.pdf", "b.pdf"]
    with pytest.raises(LibraryError, match="no es un PDF"):
        library.add_pdfs([tmp_path / "notas.txt"])


def test_background_processing_outlives_the_call_and_records_its_outcome(library, tmp_path):
    import time

    unreadable = tmp_path / "roto.pdf"
    unreadable.write_bytes(b"not a pdf")
    library.add_pdfs([unreadable])

    job = library.start_processing()
    assert job["estado"] == "en_curso"
    with pytest.raises(LibraryError, match="en curso"):
        library.start_processing()

    deadline = time.monotonic() + 60
    while library.job()["estado"] == "en_curso" and time.monotonic() < deadline:
        time.sleep(0.5)

    job = library.job()
    assert job["estado"] == "terminado", library.log_file.read_text(encoding="utf-8")
    assert job["fallidos"] == 1
    assert [p.name for p in library.pending_pdfs()] == ["roto.pdf"]
