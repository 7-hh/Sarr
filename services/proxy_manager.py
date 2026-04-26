from pathlib import Path


class ProxyManager:
    def __init__(self, path: str = "data/proxies.txt"):
        self.path = Path(path)
        self._proxies: list[str] = []
        self._idx = 0
        self.reload()

    def reload(self) -> None:
        if not self.path.exists():
            self._proxies = []
            return
        lines = [line.strip() for line in self.path.read_text(encoding="utf-8").splitlines()]
        self._proxies = [line for line in lines if line and not line.startswith("#")]

    def next_proxy(self) -> str | None:
        if not self._proxies:
            return None
        proxy = self._proxies[self._idx % len(self._proxies)]
        self._idx += 1
        return proxy
