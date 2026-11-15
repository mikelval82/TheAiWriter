from ai_writer.processors.quotes import QuoteChecker, explain_mismatch, find_quote, normalize

TEXT = (
    "Empathy is a multidimensional construct that involves both affective sharing and\n"
    "cognitive perspective taking. Several studies show that self-report measures of empa-\n"
    "thy correlate only weakly with behavioural tasks, which “challenges the idea of a\n"
    "single trait” — a point made repeatedly. The ﬁnal model explained twelve percent\n"
    "of the variance in prosocial helping across all samples. Participants were recruited online."
)


def test_exact_match():
    assert find_quote("Empathy is a multidimensional construct that involves both affective sharing", TEXT)


def test_line_breaks_and_hyphenation():
    assert find_quote("self-report measures of empathy correlate only weakly with behavioural tasks", TEXT)


def test_curly_quotes_and_dashes():
    assert find_quote('"challenges the idea of a single trait" - a point made repeatedly', TEXT)


def test_ligatures():
    assert find_quote("The final model explained twelve percent of the variance", TEXT)


def test_ellipsis_fragments_in_order():
    quote = "Empathy is a multidimensional construct … correlate only weakly with behavioural tasks"
    assert find_quote(quote, TEXT)
    assert find_quote(quote.replace("…", "[...]"), TEXT)


def test_ellipsis_fragments_out_of_order():
    assert not find_quote("correlate only weakly with behavioural tasks ... Empathy is a multidimensional construct", TEXT)


def test_bracketed_insertion():
    assert find_quote("Several studies [have shown] that self-report measures of empathy correlate only weakly", TEXT)


def test_one_character_noise():
    assert find_quote("The final model explained tvelve percent of the variance in prosocial helping", TEXT)
    assert find_quote("the final model explained twelve percent 12 of the variance in prosocial helping", TEXT)


def test_paraphrase_rejected():
    assert not find_quote("Self-reported empathy scores barely track what people actually do in behavioural tests", TEXT)


def test_too_short_rejected():
    assert not find_quote("Participants were recruited", TEXT)
    assert not find_quote("Participants were recruited online ... of the", TEXT)


def test_second_fragment_absent_rejected():
    assert not find_quote("Empathy is a multidimensional construct … explained entirely by oxytocin levels in blood", TEXT)


def test_empty_inputs():
    assert not find_quote("", TEXT)
    assert not find_quote("Participants were recruited online", "")
    assert not find_quote(None, TEXT)


def test_checker_reuses_normalised_text():
    checker = QuoteChecker(normalize(TEXT), normalized=True)
    assert checker.has("Participants were recruited online by the team") is False
    assert checker.has("of the variance in prosocial helping across all samples")


def test_explain_mismatch_replaced_word() -> None:
    passage = "The model explained twelve percent of the variance."
    quote = "The model explained twenty percent of the variance."
    result = explain_mismatch(quote, f"Earlier findings were mixed. {passage} More work follows.")
    assert result == {
        "pasaje": passage,
        "parecido": 0.88,
        "diferencias": [{"cita": "twenty", "texto": "twelve"}],
    }


def test_explain_mismatch_dropped_word() -> None:
    passage = "The final model explained twelve percent of the variance."
    result = explain_mismatch("The model explained twelve percent of the variance.", passage)
    assert result is not None
    assert result["pasaje"] == passage
    assert result["diferencias"] == [{"cita": "", "texto": "final"}]


def test_explain_mismatch_extra_word() -> None:
    passage = "The model explained twelve percent of the variance."
    result = explain_mismatch("The final model explained twelve percent of the variance.", passage)
    assert result is not None
    assert result["pasaje"] == passage
    assert result["diferencias"] == [{"cita": "final", "texto": ""}]


def test_explain_mismatch_preserves_original_characters() -> None:
    result = explain_mismatch(
        "THE model explains a large effect", "“The model”\nexplains a small effect."
    )
    assert result is not None
    assert result["pasaje"] == "“The model” explains a small effect."
    assert result["diferencias"] == [{"cita": "large", "texto": "small"}]


def test_explain_mismatch_unrelated_or_short_quote() -> None:
    assert explain_mismatch("Distant planets orbit bright stars", TEXT) is None
    assert explain_mismatch("The ocean contains many fish", "The model explained variance") is None
    assert explain_mismatch("Participants were recruited", TEXT) is None
    assert explain_mismatch("", TEXT) is None
    assert explain_mismatch("Participants were recruited online", "") is None


def test_explain_mismatch_long_text() -> None:
    filler = "Background research discusses several other topics in detail. " * 2000
    passage = "Participants demonstrated greater empathy after the experimental intervention."
    text = filler + passage + " " + filler
    quote = "Participants demonstrated lower empathy after the experimental intervention."
    result = explain_mismatch(quote, text)
    assert result is not None
    assert result["pasaje"] == passage
    assert result["diferencias"] == [{"cita": "lower", "texto": "greater"}]
