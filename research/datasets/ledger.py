"""Consultation ledger and OOS status (G00 section 10, A01 section 6).

Rules enforced here:

- the baseline status table reproduces the G00 ledger and is the starting
  point; nothing is ever promoted to ATTESTED_VIRGIN without an explicit owner
  attestation record;
- absence of local consultations never implies virginity;
- the ledger file is append-only JSON Lines; records are validated on read.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from research.datasets.contracts import (
    DatasetIntegrityError,
    OOSStatus,
    Partition,
    require,
    require_sha256,
    require_text,
)
from research.datasets.manifest import canonical_json

LEDGER_RELATIVE_PATH = "ledger/consultations.jsonl"


@dataclass(frozen=True, slots=True)
class BaselineStatus:
    instrument: str
    period: str
    status: OOSStatus
    evidence: str


# Reproduces P04-R01-G00 section 10 exactly; D00 adds no promotion.
BASELINE_LEDGER: tuple[BaselineStatus, ...] = (
    BaselineStatus("EURUSD", "2010-01..2018-06", OOSStatus.CONSULTED, "audit probes T1-T3"),
    BaselineStatus("XAUUSD", "2016-01..2024-05", OOSStatus.CONSULTED, "audit probe T4"),
    BaselineStatus("XAUUSD", "2022-06..2026-09", OOSStatus.CONSULTED, "MQL5 V19.12.1 replay"),
    BaselineStatus("EURUSD", "unknown", OOSStatus.CONSULTED, "V19 universe; V22 dashboards"),
    BaselineStatus("XAUUSD", "unknown", OOSStatus.CONSULTED, "V19 universe; V22 dashboards"),
    BaselineStatus("USDJPY", "unknown", OOSStatus.CONSULTED, "V19 InpMasterSymbols since 19.2.2"),
    BaselineStatus(
        "GBPUSD",
        "unknown",
        OOSStatus.UNVERIFIED_NOT_ATTESTED_VIRGIN,
        "no EPIP artifact found; MT5 history caches exist",
    ),
)


@dataclass(frozen=True, slots=True)
class Consultation:
    dataset_id: str
    dataset_digest: str
    experiment_id: str
    purpose: str
    consulted_at_utc: str
    partition: Partition
    outputs: tuple[str, ...]

    def __post_init__(self) -> None:
        require_sha256(self.dataset_id, "dataset_id")
        require_sha256(self.dataset_digest, "dataset_digest")
        require_text(self.experiment_id, "experiment_id")
        require_text(self.purpose, "purpose")
        require(
            type(self.consulted_at_utc) is str
            and len(self.consulted_at_utc) == 20
            and self.consulted_at_utc.endswith("Z"),
            "consulted_at_utc must be YYYY-MM-DDTHH:MM:SSZ",
        )
        require(type(self.partition) is Partition, "partition invalid")
        require(all(type(o) is str and o for o in self.outputs), "outputs invalid")

    def to_record(self) -> bytes:
        return canonical_json(
            {
                "dataset_id": self.dataset_id,
                "dataset_digest": self.dataset_digest,
                "experiment_id": self.experiment_id,
                "purpose": self.purpose,
                "consulted_at_utc": self.consulted_at_utc,
                "partition": self.partition.value,
                "outputs": list(self.outputs),
            }
        )


class ConsultationLedger:
    def __init__(self, data_root: Path) -> None:
        self._path = data_root.joinpath(*LEDGER_RELATIVE_PATH.split("/"))

    def append(self, consultation: Consultation) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "ab") as handle:
            handle.write(consultation.to_record())

    def records(self) -> tuple[Consultation, ...]:
        if not self._path.is_file():
            return ()
        out = []
        for number, line in enumerate(self._path.read_bytes().splitlines(), 1):
            try:
                data = json.loads(line)
                require(isinstance(data, dict), f"ledger line {number} is not an object")
                consultation = Consultation(
                    data["dataset_id"],
                    data["dataset_digest"],
                    data["experiment_id"],
                    data["purpose"],
                    data["consulted_at_utc"],
                    Partition(data["partition"]),
                    tuple(data["outputs"]),
                )
            except (ValueError, KeyError, TypeError) as exc:
                if isinstance(exc, DatasetIntegrityError):
                    raise
                raise DatasetIntegrityError(f"ledger line {number} is corrupted ({exc})") from exc
            require(consultation.to_record() == line + b"\n", f"ledger line {number} not canonical")
            out.append(consultation)
        return tuple(out)


def instrument_status(instrument: str, attestations: frozenset[str] = frozenset()) -> OOSStatus:
    """Most conservative status for ``instrument``.

    ``ATTESTED_VIRGIN`` requires an explicit owner attestation AND no CONSULTED
    baseline row; otherwise the baseline (or UNVERIFIED) applies.
    """
    rows = [r for r in BASELINE_LEDGER if r.instrument == instrument]
    if any(r.status is OOSStatus.CONSULTED for r in rows):
        return OOSStatus.CONSULTED
    if instrument in attestations:
        return OOSStatus.ATTESTED_VIRGIN
    return OOSStatus.UNVERIFIED_NOT_ATTESTED_VIRGIN
