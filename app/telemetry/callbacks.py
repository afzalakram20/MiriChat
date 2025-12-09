import time, structlog


log = structlog.get_logger()


class Trace:
    def __init__(self, request_id: str):
        self.request_id = request_id


def span(self, name: str):
    return _Span(name, self.request_id)


class _Span:
    def __init__(self, name: str, request_id: str):
        self.name = name
        self.request_id = request_id


def __enter__(self):
    self.start = time.time()
    return self


def __exit__(self, exc_type, exc, tb):
    dur = int((time.time() - self.start) * 1000)
    log.info("span", request_id=self.request_id, name=self.name, duration_ms=dur)