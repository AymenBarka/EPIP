"""P04-R01-D01-B1 acquisition locks and the one-window gate (offline, synthetic).

Covers atomic exclusive locking per window and per data root, refusal before any
transport call, release on success and on exceptions, fail-closed stale-lock
recovery, ownership protection, resume, the daily budget, dry runs, and genuine
concurrent processes.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest

from research.datasets import acquisition, cli
from research.datasets.acquisition import (
    GLOBAL_LOCK_NAME,
    LOCKS_RELATIVE_DIR,
    AcquisitionLock,
    AuthorizedWindow,
    DailyRequestBudget,
    FetchStatus,
    HttpResponse,
    LockState,
    authorized_window,
    inspect_locks,
    process_state,
    release_stale_lock,
    run_acquisition,
)
from research.datasets.batches import D01_B1, OPEN_WINDOWS, batch_windows, governed_window
from research.datasets.contracts import MS_PER_HOUR, DatasetIntegrityError
from research.tests.fixtures import FakeClock, FakeTransport
from research.tests.test_d00_acquisition import sample_responder
from research.tests.test_d01_b1 import month_responder

REPO_ROOT = Path(__file__).resolve().parents[2]
EUR_JAN = governed_window("D01-B1-EURUSD-2018-01")


def short(window: AuthorizedWindow, days: int = 1) -> AuthorizedWindow:
    return replace(window, tick_end_ms=window.tick_start_ms + days * 24 * MS_PER_HOUR)


def forbidden(_url: str, _budget: int) -> HttpResponse:
    raise AssertionError("transport must not be invoked")


def lock_files(root: Path) -> list[str]:
    directory = root / LOCKS_RELATIVE_DIR
    return sorted(p.name for p in directory.glob("*")) if directory.is_dir() else []


def write_lock(root: Path, name: str, **owner: object) -> Path:
    path = root / LOCKS_RELATIVE_DIR / f"{name}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(owner), encoding="ascii")
    return path


def finished_pid() -> int:
    probe = subprocess.Popen([sys.executable, "-c", "pass"])
    probe.wait()
    return probe.pid


def spawn(code: str) -> subprocess.Popen[str]:
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.Popen(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )


def wait_for(path: Path, timeout_s: float = 60.0) -> None:
    deadline = time.monotonic() + timeout_s
    while not path.exists():
        assert time.monotonic() < deadline, f"timed out waiting for {path}"
        time.sleep(0.02)


HOLDER = """
import sys
from pathlib import Path
from research.datasets.acquisition import AcquisitionLock
root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path({root!r})
locks = [AcquisitionLock(root, name, {window!r}, "2026-11-25T00:00:00Z").acquire()
         for name in {names!r}]
import os
print("HELD", os.getpid(), flush=True)
sys.stdin.readline()
for lock in reversed(locks):
    lock.release()
"""


# --- gate boundary ---------------------------------------------------------------
def test_exactly_one_window_is_open() -> None:
    assert OPEN_WINDOWS == frozenset({"D01-B1-EURUSD-2018-01"})
    matrix = {w.window_id: w.acquisition_open for w in batch_windows(D01_B1)}
    assert len(matrix) == 12 and [k for k, v in matrix.items() if v] == ["D01-B1-EURUSD-2018-01"]
    assert EUR_JAN.tick_start_ms == 1_514_764_800_000  # 2018-01-01T00:00:00Z
    assert EUR_JAN.tick_end_ms == 1_517_443_200_000  # 2018-02-01T00:00:00Z
    assert (EUR_JAN.max_planned_requests, EUR_JAN.max_requests, EUR_JAN.max_bytes) == (
        600,
        1500,
        100_000_000,
    )
    limits = acquisition.limits_for(EUR_JAN)
    assert limits.min_interval_s >= 1.0 and limits.max_retries == 4 and limits.timeout_s == 30
    assert authorized_window("A01-SAMPLE-2012-03").acquisition_open is True  # D00 unchanged


def test_cli_open_window_still_requires_terms_and_dry_run_has_no_side_effects(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def no_transport() -> object:
        raise AssertionError("transport must not be created")

    args = ["acquire", "--window", EUR_JAN.window_id, "--data-root", str(tmp_path)]
    assert cli.main(args, no_transport) == 1  # type: ignore[arg-type]
    assert "--confirm-provider-terms" in capsys.readouterr().err
    assert cli.main([*args, "--dry-run"], no_transport) == 0  # type: ignore[arg-type]
    plan = json.loads(capsys.readouterr().out)
    assert (plan["requests"], plan["acquisition_gate"]) == (554, "OPEN")
    assert not any(tmp_path.iterdir())


def test_cli_confirmed_run_reaches_transport_under_locks_and_releases(tmp_path: Path) -> None:
    class Boom(RuntimeError):
        pass

    seen: list[list[str]] = []

    class Probe:
        def get(self, url: str, timeout_s: float, max_bytes: int) -> HttpResponse:
            seen.append(lock_files(tmp_path))
            assert url.endswith("/EURUSD/2018/00/01/00h_ticks.bi5") and timeout_s == 30
            raise Boom

    args = ["acquire", "--window", EUR_JAN.window_id, "--data-root", str(tmp_path)]
    with pytest.raises(Boom):
        cli.main([*args, "--confirm-provider-terms"], Probe)
    assert seen == [["D01-B1-EURUSD-2018-01.lock", "global.lock"]]
    assert lock_files(tmp_path) == []
    assert DailyRequestBudget(tmp_path).used(time.strftime("%Y-%m-%d", time.gmtime())) == 1


# --- lock mechanics ----------------------------------------------------------------
def test_exclusive_lock_records_owner_and_refuses_a_second_holder(tmp_path: Path) -> None:
    lock = AcquisitionLock(tmp_path, "w1", "w1", "2026-11-25T00:00:00Z").acquire()
    owner = json.loads(lock.path.read_text("ascii"))
    assert owner == {
        "acquired_utc": "2026-11-25T00:00:00Z",
        "executable": sys.executable,
        "host": socket.gethostname(),
        "lock": "w1",
        "pid": os.getpid(),
        "token": lock.token,
        "window": "w1",
    }
    with pytest.raises(DatasetIntegrityError, match="lock w1 is held"):
        AcquisitionLock(tmp_path, "w1", "w1", "t").acquire()
    assert json.loads(lock.path.read_text("ascii"))["token"] == lock.token
    lock.release()
    lock.release()  # idempotent once released
    assert not lock.path.exists()
    with pytest.raises(DatasetIntegrityError, match="invalid lock name"):
        AcquisitionLock(tmp_path, "../x", "w", "t")


def test_failed_metadata_write_leaves_no_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(_fd: int) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "fsync", broken)
    lock = AcquisitionLock(tmp_path, "w1", "w1", "t")
    with pytest.raises(OSError, match="disk full"):
        lock.acquire()
    assert not lock.path.exists() and lock.held is False


def test_refusal_happens_before_transport_and_budget(tmp_path: Path) -> None:
    window = short(EUR_JAN)
    budget = DailyRequestBudget(tmp_path)
    for name in (window.window_id, GLOBAL_LOCK_NAME):
        held = AcquisitionLock(tmp_path, name, "other", "t").acquire()
        with pytest.raises(DatasetIntegrityError, match=f"lock {name} is held"):
            run_acquisition(
                window, tmp_path, FakeTransport(forbidden), FakeClock(), daily_budget=budget
            )
        assert lock_files(tmp_path) == [f"{name}.lock"]  # the refused run removed nothing
        held.release()
    assert not (tmp_path / "acquisition/daily_requests.jsonl").exists()
    assert not (tmp_path / "acquisition/journal.jsonl").exists()


def test_locks_released_after_success_and_after_exceptions(tmp_path: Path) -> None:
    window = short(EUR_JAN)
    clock = FakeClock()
    report = run_acquisition(window, tmp_path, FakeTransport(month_responder(), clock=clock), clock)
    assert report.aborted is None and lock_files(tmp_path) == []

    def explode(_url: str, _budget: int) -> HttpResponse:
        raise KeyboardInterrupt

    other = tmp_path / "other"
    with pytest.raises(KeyboardInterrupt):
        run_acquisition(window, other, FakeTransport(explode), FakeClock())
    assert lock_files(other) == []


def test_foreign_owner_is_never_removed(tmp_path: Path) -> None:
    window = short(EUR_JAN)
    path = tmp_path / LOCKS_RELATIVE_DIR / f"{window.window_id}.lock"

    def hijack(url: str, budget: int) -> HttpResponse:
        owner = json.loads(path.read_text("ascii"))
        path.write_text(json.dumps({**owner, "token": "foreign"}), encoding="ascii")
        raise RuntimeError("stop")

    with pytest.raises(DatasetIntegrityError, match="no longer owned by this process"):
        run_acquisition(window, tmp_path, FakeTransport(hijack), FakeClock())
    assert json.loads(path.read_text("ascii"))["token"] == "foreign"
    assert lock_files(tmp_path) == [f"{window.window_id}.lock", "global.lock"]


# --- stale locks and recovery ----------------------------------------------------------
def test_stale_lock_is_detected_but_never_removed_automatically(tmp_path: Path) -> None:
    window = short(EUR_JAN)
    clock = FakeClock()
    run_acquisition(window, tmp_path, FakeTransport(month_responder(), clock=clock), clock)
    raw = tmp_path / "raw/dukascopy/EURUSD/ticks/2018/01/01/00h_ticks.bi5"
    before = raw.read_bytes()
    dead = finished_pid()
    owner = {"host": socket.gethostname(), "pid": dead, "token": "t-dead", "window": "x"}
    write_lock(tmp_path, GLOBAL_LOCK_NAME, **owner)
    (info,) = inspect_locks(tmp_path)
    assert (info.name, info.state, info.owner["token"]) == (
        "global",
        LockState.NOT_RUNNING,
        "t-dead",
    )
    with pytest.raises(DatasetIntegrityError, match="lock global is held"):
        run_acquisition(window, tmp_path, FakeTransport(forbidden), FakeClock())
    with pytest.raises(DatasetIntegrityError, match="token does not match"):
        release_stale_lock(tmp_path, GLOBAL_LOCK_NAME, "guess")
    release_stale_lock(tmp_path, GLOBAL_LOCK_NAME, "t-dead")
    assert inspect_locks(tmp_path) == ()
    with pytest.raises(DatasetIntegrityError, match="no acquisition lock"):
        release_stale_lock(tmp_path, GLOBAL_LOCK_NAME, "t-dead")
    resumed = run_acquisition(window, tmp_path, FakeTransport(forbidden), FakeClock())
    assert {s for _, s in resumed.outcomes} == {FetchStatus.SKIPPED_VERIFIED}
    assert resumed.requests_used == 0 and raw.read_bytes() == before


@pytest.mark.parametrize(
    ("owner", "state"),
    [
        ({"host": "another-host", "pid": 1, "token": "t"}, LockState.UNKNOWN),
        ({"host": "SELF", "pid": "1", "token": "t"}, LockState.UNKNOWN),
        ({"host": "SELF", "pid": "SELF", "token": "t"}, LockState.ALIVE),
        (None, LockState.UNKNOWN),
        ([1, 2], LockState.UNKNOWN),
    ],
)
def test_unverifiable_or_live_owners_fail_closed(
    tmp_path: Path, owner: object, state: LockState
) -> None:
    path = tmp_path / LOCKS_RELATIVE_DIR / "global.lock"
    path.parent.mkdir(parents=True)
    if isinstance(owner, dict):
        owner = {
            k: (socket.gethostname() if v == "SELF" and k == "host" else v)
            for k, v in owner.items()
        }
        owner = {k: (os.getpid() if v == "SELF" else v) for k, v in owner.items()}
        path.write_text(json.dumps(owner), encoding="ascii")
    elif owner is None:
        path.write_bytes(b"{corrupted")
    else:
        path.write_text(json.dumps(owner), encoding="ascii")
    (info,) = inspect_locks(tmp_path)
    assert info.state is state
    with pytest.raises(DatasetIntegrityError, match=r"not removed|cannot be cleared"):
        release_stale_lock(tmp_path, GLOBAL_LOCK_NAME, "t")
    assert path.exists()


def test_process_state_probes(monkeypatch: pytest.MonkeyPatch) -> None:
    assert process_state(os.getpid()) is LockState.ALIVE
    assert process_state(finished_pid()) is LockState.NOT_RUNNING
    assert process_state(0) is LockState.UNKNOWN
    assert process_state(True) is LockState.UNKNOWN
    for error, state in ((PermissionError(), LockState.ALIVE), (OSError(), LockState.UNKNOWN)):

        def raising(_pid: int, _sig: int, error: OSError = error) -> None:
            raise error

        monkeypatch.setattr(os, "kill", raising)
        assert process_state(12345, platform="linux") is state


class FakeKernel32:
    def __init__(self, handle: int, exit_code: int, query_ok: bool = True) -> None:
        self.handle, self.exit_code, self.query_ok = handle, exit_code, query_ok
        self.closed: list[int] = []

    def OpenProcess(self, access: int, inherit: bool, pid: int) -> int:
        assert (access, inherit) == (0x1000, False)
        return self.handle

    def GetExitCodeProcess(self, handle: int, code: object) -> bool:
        code._obj.value = self.exit_code  # type: ignore[attr-defined]
        return self.query_ok

    def CloseHandle(self, handle: int) -> None:
        self.closed.append(handle)


@pytest.mark.parametrize(
    ("kernel", "error", "state"),
    [
        (FakeKernel32(7, 259), 0, LockState.ALIVE),
        (FakeKernel32(7, 0), 0, LockState.NOT_RUNNING),
        (FakeKernel32(7, 259, query_ok=False), 0, LockState.UNKNOWN),
        (FakeKernel32(0, 0), 87, LockState.NOT_RUNNING),
        (FakeKernel32(0, 0), 5, LockState.ALIVE),
        (FakeKernel32(0, 0), 6, LockState.UNKNOWN),
    ],
)
def test_windows_probe_never_signals(kernel: FakeKernel32, error: int, state: LockState) -> None:
    result = process_state(4242, platform="win32", kernel32=kernel, last_error=lambda: error)
    assert result is state
    assert kernel.closed == ([7] if kernel.handle else [])


# --- genuine concurrent processes -------------------------------------------------------
def test_concurrent_process_holding_the_same_window_blocks_acquisition(tmp_path: Path) -> None:
    window = short(EUR_JAN)
    child = spawn(
        HOLDER.format(root=str(tmp_path), window=window.window_id, names=[window.window_id])
    )
    try:
        assert child.stdout is not None
        word, pid = child.stdout.readline().split()
        # On Windows a venv python.exe is a launcher: the interpreter is its child.
        (info,) = inspect_locks(tmp_path)
        assert word == "HELD" and info.state is LockState.ALIVE and info.owner["pid"] == int(pid)
        with pytest.raises(DatasetIntegrityError, match=f"lock {window.window_id} is held"):
            run_acquisition(window, tmp_path, FakeTransport(forbidden), FakeClock())
        with pytest.raises(DatasetIntegrityError, match="state ALIVE"):
            release_stale_lock(tmp_path, window.window_id, str(info.owner["token"]))
    finally:
        child.communicate("\n", timeout=60)
    assert child.returncode == 0 and lock_files(tmp_path) == []
    clock = FakeClock()
    report = run_acquisition(window, tmp_path, FakeTransport(month_responder(), clock=clock), clock)
    assert report.aborted is None


def test_concurrent_process_on_another_window_blocks_the_data_root(tmp_path: Path) -> None:
    child = spawn(
        HOLDER.format(
            root=str(tmp_path),
            window="D01-B1-XAUUSD-2018-01",
            names=[GLOBAL_LOCK_NAME, "D01-B1-XAUUSD-2018-01"],
        )
    )
    budget = DailyRequestBudget(tmp_path)
    try:
        assert child.stdout is not None and child.stdout.readline().startswith("HELD ")
        with pytest.raises(DatasetIntegrityError, match="lock global is held"):
            run_acquisition(
                short(EUR_JAN), tmp_path, FakeTransport(forbidden), FakeClock(), daily_budget=budget
            )
    finally:
        child.communicate("\n", timeout=60)
    assert child.returncode == 0 and lock_files(tmp_path) == []
    assert budget.used("2026-11-22") == 0


RACER = """
import sys, time
from pathlib import Path
from research.datasets.acquisition import AcquisitionLock
from research.datasets.contracts import DatasetIntegrityError
root, go = Path(sys.argv[1]), Path(sys.argv[2])
while not go.exists():
    time.sleep(0.001)
try:
    lock = AcquisitionLock(root, "race", "race", "t").acquire()
except DatasetIntegrityError:
    print("REFUSED", flush=True)
else:
    print("WON", flush=True)
    sys.stdin.readline()
    lock.release()
"""


def test_atomic_contention_admits_exactly_one_process(tmp_path: Path) -> None:
    go = tmp_path / "go"
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    racers = [
        subprocess.Popen(
            [sys.executable, "-c", RACER, str(tmp_path), str(go)],
            cwd=REPO_ROOT,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        for _ in range(6)
    ]
    time.sleep(0.5)
    go.write_text("go", encoding="ascii")
    lines = []
    for racer in racers:
        assert racer.stdout is not None
        lines.append(racer.stdout.readline().strip())
    for racer in racers:
        racer.communicate("\n", timeout=60)
    assert sorted(lines) == ["REFUSED"] * 5 + ["WON"]
    assert all(r.returncode == 0 for r in racers)
    assert lock_files(tmp_path) == []


def test_d00_acquisition_leaves_no_locks(tmp_path: Path) -> None:
    window = authorized_window("A01-SAMPLE-2012-03")
    clock = FakeClock()
    report = run_acquisition(window, tmp_path, FakeTransport(sample_responder, clock=clock), clock)
    assert report.aborted is None and report.requests_used == 244
    assert lock_files(tmp_path) == [] and inspect_locks(tmp_path) == ()
    assert inspect_locks(tmp_path / "never-used") == ()
