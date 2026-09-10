"""
Boots a profile's own local dev/build server so a website's REPO — not a
live URL — can be audited before it's deployed. The engine only knows how
to run an arbitrary shell command and poll a URL until it's ready; it has
zero framework-specific auto-detection (booting Next.js vs. WordPress-via-
Docker vs. a plain static-file server is inherently profile-owned — see a
profile's `local_dev` block in site.yaml).

Once the target is serving, the crawl itself is IDENTICAL to a live-URL
crawl — local-serve only changes how bytes get fetched, never a downstream
code path (the resulting site dict has the same shape either way).
"""
import os
import signal
import subprocess
import time
import urllib.request
from dataclasses import dataclass


class LocalServeError(RuntimeError):
    pass


@dataclass
class LocalDevConfig:
    start_command: str
    port: int
    ready_url: str
    cwd: str | None = None
    ready_timeout_s: float = 60.0
    stop_command: str | None = None

    @classmethod
    def from_profile_dict(cls, local_dev: dict, profile_root) -> "LocalDevConfig":
        if not local_dev.get("start_command"):
            raise LocalServeError(
                "This profile has no local_dev.start_command in site.yaml — "
                "local-serve mode needs one (e.g. \"npm run dev\")."
            )
        return cls(
            start_command=local_dev["start_command"],
            port=local_dev["port"],
            ready_url=local_dev.get("ready_url") or f"http://localhost:{local_dev['port']}/",
            cwd=local_dev.get("cwd") or str(profile_root),
            ready_timeout_s=float(local_dev.get("ready_timeout_s", 60.0)),
            stop_command=local_dev.get("stop_command"),
        )


class LocalServer:
    """Context manager: start the profile's dev server, wait until it
    answers `ready_url`, hand back the base URL to crawl — then tear it
    down (explicit stop_command, or SIGTERM to the whole process group) on
    exit, whether or not the crawl itself succeeded."""

    def __init__(self, config: LocalDevConfig):
        self.config = config
        self._proc: subprocess.Popen | None = None

    def __enter__(self) -> str:
        self._proc = subprocess.Popen(
            self.config.start_command,
            shell=True,
            cwd=self.config.cwd,
            start_new_session=True,  # own process group, so teardown can kill children too
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self._wait_until_ready()
        return f"http://localhost:{self.config.port}"

    def _wait_until_ready(self) -> None:
        deadline = time.time() + self.config.ready_timeout_s
        last_error: Exception | None = None
        while time.time() < deadline:
            if self._proc.poll() is not None:
                out = self._proc.stdout.read() if self._proc.stdout else ""
                raise LocalServeError(
                    f"'{self.config.start_command}' exited early (code {self._proc.returncode}) "
                    f"before becoming ready:\n{out}"
                )
            try:
                urllib.request.urlopen(self.config.ready_url, timeout=1).read()
                return
            except Exception as e:  # noqa: BLE001 - any failure just means "not ready yet"
                last_error = e
                time.sleep(0.3)
        self.__exit__(None, None, None)
        raise LocalServeError(
            f"{self.config.ready_url} never became ready within {self.config.ready_timeout_s}s: {last_error}"
        )

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._proc is None or self._proc.poll() is not None:
            return
        if self.config.stop_command:
            subprocess.run(self.config.stop_command, shell=True, cwd=self.config.cwd)
            self._proc.wait(timeout=10)
        else:
            try:
                os.killpg(os.getpgid(self._proc.pid), signal.SIGTERM)
                self._proc.wait(timeout=10)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                os.killpg(os.getpgid(self._proc.pid), signal.SIGKILL)
