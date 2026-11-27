from .mocks import unavailable


def ask_agent(*_args, **_kwargs):
    return unavailable("Agent service")
