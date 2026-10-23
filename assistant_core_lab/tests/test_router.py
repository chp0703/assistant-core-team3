"""Router tests placeholder for a later lab step."""

from assistant_core.models import Intent
from assistant_core.router import route


def test_route_greeting():
    assert route("Hello!", set()) == Intent.GREETING


def test_route_fee():
    assert route("tuition for 18 credits", set()) == Intent.FEE


def test_route_office():
    office_names = {"library", "registrar"}
    assert route("Where is the library?", office_names) == Intent.OFFICE


def test_route_rule():
    assert route("Can I register my thesis?", set()) == Intent.RULE
