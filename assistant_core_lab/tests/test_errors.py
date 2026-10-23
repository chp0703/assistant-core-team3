"""Verify that callers can catch shared errors without losing their type."""

import pytest

from assistant_core.errors import AssistantError, ConfigError, DataError, InvalidRequest, ProviderError


@pytest.mark.parametrize("error_type", [ConfigError, DataError, InvalidRequest, ProviderError])
def test_named_errors_can_be_caught_as_assistant_errors(error_type: type[AssistantError]) -> None:
    error = error_type("Actionable failure details.")

    with pytest.raises(AssistantError) as caught:
        raise error

    assert type(caught.value) is error_type
    assert str(caught.value) == "Actionable failure details."
