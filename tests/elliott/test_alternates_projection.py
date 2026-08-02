from epip.elliott import ElliottConfig
from epip.elliott.analyzer import ElliottAnalyzer
from epip.elliott.models import CountStatus, WaveLabel
from tests.elliott.helpers import market_context


def test_alternates_and_projection_are_deterministic() -> None:
    context = market_context()
    analyzer = ElliottAnalyzer(ElliottConfig())
    first = analyzer.analyze(context)
    second = analyzer.analyze(context)
    assert first == second
    assert first.alternates[0].count.status == CountStatus.ALTERNATE
    assert first.projection is not None
    assert first.projection.next_wave == WaveLabel.A
    assert first.projection.targets


def test_empty_wave_set_has_no_projection_or_alternate() -> None:
    analysis = ElliottAnalyzer(ElliottConfig()).analyze(market_context((1.0,)))
    assert analysis.alternates == ()
    assert analysis.projection is None
