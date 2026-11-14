from ai_writer.processors.quotes import QuoteChecker, find_quote, normalize

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
