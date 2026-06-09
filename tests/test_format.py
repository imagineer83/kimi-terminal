from kimi_terminal.utils.format import color_for_change, fmt_change, fmt_pct, fmt_price, fmt_volume


def test_fmt_price():
    assert fmt_price(1500.5) == "1,500.50"
    assert fmt_price(None) == "-"


def test_fmt_change():
    assert fmt_change(5.2) == "+5.20"
    assert fmt_change(-3.1) == "-3.10"


def test_fmt_volume():
    assert fmt_volume(1_5000_0000) == "1.50亿"
    assert fmt_volume(5_0000) == "5.00万"


def test_color_for_change():
    assert color_for_change(1.0) == "red"
    assert color_for_change(-1.0) == "green"
    assert color_for_change(0.0) == "white"
