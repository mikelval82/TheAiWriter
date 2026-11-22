"""Segmentation: ordered, non-overlapping cuts without administrative text."""

import random

from ai_writer.segmentation import segment


def words(n: int, tag: str = "w") -> str:
    return " ".join(f"{tag}{i}" for i in range(n))


def paper(sections: list[tuple[str, int]], numbered: bool = False, refs: bool = True) -> str:
    parts = ["Title of the paper\nA. Author, B. Author"]
    for i, (name, n) in enumerate(sections, 1):
        head = f"{i}. {name}" if numbered else name
        parts.append(f"{head}\n{words(n, name[:3])}")
    if refs:
        parts.append("References\n[1] Someone. A cited work. 2020.")
    return "\n\n".join(parts)


def test_missing_middle_heading_no_overlap_full_coverage():
    text = paper([("Introduction", 200), ("Methods", 200), ("Results", 200), ("Discussion", 200)])
    names = ["Introduction", "Methods", "Missing section", "Results", "Discussion"]
    segs = segment(text, names)
    assert [s.name for s in segs] == ["Introduction", "Methods", "Results", "Discussion"]
    assert [s.number for s in segs] == [1, 2, 3, 4]
    for a, b in zip(segs, segs[1:]):
        assert a.end <= b.start
    joined = " ".join(s.content for s in segs)
    for tag in ("Int", "Met", "Res", "Dis"):
        assert f"{tag}199" in joined and f"{tag}0 " in joined
    assert "Someone" not in joined


def test_missing_heading_text_stays_in_previous_segment():
    text = paper([("Introduction", 200), ("Methods", 200), ("Results", 200)])
    segs = segment(text, ["Introduction", "Nope", "Results"])
    assert [s.name for s in segs] == ["Introduction", "Results"]
    assert "Met199" in segs[0].content


def test_numbered_headings():
    text = paper([("Introduction", 200), ("Related Work", 200)], numbered=True)
    segs = segment(text, ["Introduction", "related   work"])
    assert [s.name for s in segs] == ["Introduction", "related   work"]
    assert segs[0].content.startswith("Int0") and segs[0].content.endswith("Int199")
    text = "Title\n\nII. Introduction\n" + words(200) + "\n\n2.1 Methods\n" + words(200)
    assert len(segment(text, ["Introduction", "Methods"])) == 2
    assert len(segment(text, ["2. Introduction", "2.1 Methods"])) == 2


def test_references_cut_and_text_after_discarded():
    text = paper([("Introduction", 200), ("Conclusion", 200)]) + "\n\nAppendix after refs " + words(300)
    segs = segment(text, ["Introduction", "Conclusion"])
    assert [s.name for s in segs] == ["Introduction", "Conclusion"]
    assert "Someone" not in segs[-1].content and segs[-1].end <= text.index("References")


def test_appendix_after_the_references_resumes_the_body():
    text = (
        paper([("Introduction", 200), ("Conclusion", 200)])
        + "\n\nAppendix A\n" + words(300, "app") + "\n\nAppendix B\n" + words(300, "apb")
    )
    names = ["Introduction", "Conclusion", "References", "Appendix A", "Appendix B"]
    segs = segment(text, names)
    assert [s.name for s in segs] == ["Introduction", "Conclusion", "Appendix A", "Appendix B"]
    joined = " ".join(s.content for s in segs)
    assert "Someone" not in joined and "References" not in joined
    assert "app299" in segs[2].content and "apb0 " in segs[3].content
    assert segs[1].end <= text.index("References") and segs[2].start > text.index("Someone")
    for a, b in zip(segs, segs[1:]):
        assert a.end <= b.start
    assert segment(text, names[:2] + names[3:]) == segs


def test_admin_skipped_but_ethical_content_kept():
    text = paper(
        [
            ("Introduction", 200),
            ("Ethical implications of empathic AI", 200),
            ("Acknowledgements", 200),
            ("Funding", 200),
            ("Conflict of Interest", 200),
            ("Data availability statement", 200),
        ]
    )
    names = [
        "Introduction",
        "Ethical implications of empathic AI",
        "Acknowledgements",
        "Funding",
        "Conflict of Interest",
        "Data availability statement",
    ]
    segs = segment(text, names)
    assert [s.name for s in segs] == ["Introduction", "Ethical implications of empathic AI"]
    assert "Ack0" not in " ".join(s.content for s in segs)


def test_small_segment_merged_forward_and_last_merged_backward():
    text = paper([("Introduction", 200), ("Tiny", 30), ("Methods", 200), ("Outro", 20)])
    segs = segment(text, ["Introduction", "Tiny", "Methods", "Outro"])
    # Tiny goes forward into Methods; Outro (last, small) goes back into the merged one
    assert [s.name for s in segs] == ["Introduction", "Tiny / Methods / Outro"]
    assert "Tin0" in segs[1].content and "Out19" in segs[1].content
    assert segs[1].start < segs[1].end and segs[0].end <= segs[1].start


def test_big_segment_split_within_max_words():
    text = paper([("Introduction", 100), ("Methods", 0)])
    paragraphs = "\n\n".join(words(400, f"p{i}x") for i in range(8))
    text = text.replace("Methods\n", "Methods\n" + paragraphs)
    segs = segment(text, ["Introduction", "Methods"], min_words=50, max_words=1000)
    methods = [s for s in segs if s.name.startswith("Methods")]
    assert [s.name for s in methods] == ["Methods (1/4)", "Methods (2/4)", "Methods (3/4)", "Methods (4/4)"]
    assert all(len(s.content.split()) <= 1000 for s in methods)
    assert sum(len(s.content.split()) for s in methods) == 3200
    for a, b in zip(segs, segs[1:]):
        assert a.end <= b.start


def test_big_single_paragraph_splits_by_sentence_then_words():
    sentences = " ".join(f"{words(40, f's{i}')}." for i in range(50))
    segs = segment(sentences, [], min_words=10, max_words=700)
    assert len(segs) == 3 and all(len(s.content.split()) <= 700 for s in segs)
    assert all(s.content.endswith(".") for s in segs)
    blob = words(2000)
    segs = segment(blob, [], min_words=10, max_words=700)
    assert len(segs) == 3 and sum(len(s.content.split()) for s in segs) == 2000


def test_fallback_without_headings():
    text = "Some text " * 100 + "\n\nReferences\n[1] Cited."
    segs = segment(text, ["Introduction", "Methods"])
    assert [s.name for s in segs] == ["Texto"] and segs[0].number == 1
    assert "Cited" not in segs[0].content
    assert segment(text, ["Introduction"])[0].name == "Texto"


def test_empty_text():
    assert segment("", ["A"]) == []
    assert segment("  \n ", []) == []


def test_preamble_only_when_long_enough():
    short = "Title\n\n" + words(40, "abs") + "\n\nIntroduction\n" + words(200) + "\n\nMethods\n" + words(200)
    assert [s.name for s in segment(short, ["Introduction", "Methods"])] == ["Introduction", "Methods"]
    long = "Title\n\n" + words(300, "abs") + "\n\nIntroduction\n" + words(200) + "\n\nMethods\n" + words(200)
    segs = segment(long, ["Introduction", "Methods"])
    assert [s.name for s in segs] == ["Preámbulo", "Introduction", "Methods"]


def test_word_count_never_exceeds_text():
    rng = random.Random(7)
    names = ["Introduction", "Background", "Methods", "Results", "Discussion", "Conclusion"]
    for _ in range(20):
        sizes = [(n, rng.randint(0, 3000)) for n in names if rng.random() > 0.2]
        text = paper(sizes, numbered=rng.random() > 0.5)
        segs = segment(text, names)
        assert sum(len(s.content.split()) for s in segs) <= len(text.split())
        assert all(s.content.strip() for s in segs)
        assert [s.number for s in segs] == list(range(1, len(segs) + 1))
        for a, b in zip(segs, segs[1:]):
            assert a.end <= b.start
