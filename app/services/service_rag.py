from .mocks import unavailable


def ask_rag(*_args, **_kwargs):
    return unavailable("RAG service")
