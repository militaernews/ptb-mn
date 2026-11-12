from util.amounts import abbreviate_amounts


def test_abbreviate_amounts():
    assert abbreviate_amounts("Hilfe über 5 Millionen US-Dollar und 2,3 Milliarden Euro.") == (
        "Hilfe über 5 Mio. USD und 2,3 Mrd. EUR."
    )
    assert abbreviate_amounts("Ein Schaden von 1,5 Millionen. Danach 300 Dollar") == (
        "Ein Schaden von 1,5 Mio. Danach 300 USD"
    )
    assert abbreviate_amounts("Millionen Menschen, der US-Dollar fällt") == "Millionen Menschen, der US-Dollar fällt"
    assert abbreviate_amounts("2026 Euro-Scheine, 10 Mio Rubel") == "2026 Euro-Scheine, 10 Mio. RUB"
