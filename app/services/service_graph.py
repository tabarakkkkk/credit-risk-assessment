from .mocks import unavailable


def query_graph(*_args, **_kwargs):
    return unavailable("Graph service")
