"""EvidenceIndex: every observation, coverage, catalog link, and activity, queryable per case at audit_at.

The two-clock rule lives here (Observation.usable / Coverage.usable). A case's state evidence must also be
observed at or after the request (`since=requested_at`): earlier observations describe an earlier episode
(every evidence cited in the samples lies in [requested_at, audit_at]). State at audit_at = the latest such
DIRECT observation; an OMISSION proof (coverage) is used only when no DIRECT observation exists
(sample case_21 cites evidence_92's 404, not the later empty snapshot evidence_51).
"""

from collections import defaultdict
from dataclasses import dataclass, replace

from evidence import activity, documents, images, logs, records, sql
from evidence.common import load_manifest
from evidence.model import Directness, Observation, State, system_for
from evidence.ledger import EvidenceLedger


def _order(o):
    return (o.observed_at, o.file_captured_at, o.evidence_id, o.source)


@dataclass
class EvidenceIndex:
    observations: list
    coverages: list
    links: list
    activities: list
    missing_image_facts: list
    ledger: EvidenceLedger | None = None

    def __post_init__(self):
        self.by_rid = defaultdict(list)
        self.by_key = defaultdict(list)
        for o in self.observations:
            self.by_rid[o.resource_id].append(o)
            for k in o.link_keys:
                self.by_key[k].append(o)
        for lst in self.by_rid.values():
            lst.sort(key=_order)

    def usable(self, resource_id, audit_at, since=None):
        return [o for o in self.by_rid.get(resource_id, [])
                if o.usable(audit_at) and (since is None or o.observed_at >= since)]

    def matching(self, link_keys, audit_at=None):
        """Observations carrying any of the given identifier keys (usable at audit_at, or all if None)."""
        seen, out = set(), []
        for k in link_keys:
            for o in self.by_key.get(k, []):
                if id(o) not in seen and (audit_at is None or o.usable(audit_at)):
                    seen.add(id(o))
                    out.append(o)
        return sorted(out, key=_order)

    def omission(self, resource_id, audit_at, since=None):
        """Latest usable coverage that proves the resource absent, as an OMISSION observation."""
        covs = [c for c in self.coverages if c.usable(audit_at) and c.proves_absent(resource_id)
                and (since is None or c.observed_at >= since)]
        if not covs:
            return None
        c = max(covs, key=lambda c: (c.observed_at, c.file_captured_at, c.evidence_id))
        return Observation(c.evidence_id, c.file_captured_at, c.observed_at, system_for(resource_id), resource_id,
                           None, State.ABSENT, directness=Directness.OMISSION, source=c.source,
                           source_location=c.source, physical_scope=c.covered_scopes, observation_time_basis="scoped_snapshot")

    def state_at(self, resource_id, audit_at, since=None):
        """The observation that determines the resource's state at audit_at (None if nothing usable)."""
        direct = self.usable(resource_id, audit_at, since)
        if direct:
            return direct[-1]
        omission = self.omission(resource_id, audit_at, since)
        if omission is not None or since is None or system_for(resource_id) != 'account_service':
            return omission
        # Deletion may already have happened before the request. Recover the
        # most recent eligible historical absence, not an arbitrary old proof.
        historical = self.usable(resource_id, audit_at)
        older = self.omission(resource_id, audit_at)
        if older is not None:
            historical.append(older)
        if not historical:
            return None
        latest = max(historical, key=_order)
        if latest.state != State.ABSENT:
            return None
        creating = {'CREATE_RECORD', 'UPDATE_RECORD', 'SYNC_RECORD', 'INDEX_RECORD',
                    'IMPORT_RECORD', 'RESTORE_BACKUP', 'REFRESH_CACHE'}
        if any(a.resource_id == resource_id and latest.observed_at < a.event_time <= audit_at
               and a.event_type in creating for a in self.activities):
            return None
        return latest


def build(data_dir, facts_dir=images.FACTS_DIR, visual_reader=None, render_dir=None):
    manifest = load_manifest(data_dir)
    acts = activity.load_activities(data_dir)
    links = activity.catalog_links(acts)
    from evidence.ledger import extract_corpus
    from pathlib import Path
    observations, coverages, missing, ledger = extract_corpus(manifest, links, facts_dir, visual_reader,
        render_dir or Path(data_dir).resolve().parent / "diagnostics/visual_review")
    observations += activity.observations(acts)
    ledger = replace(ledger, observations=tuple(observations))
    return EvidenceIndex(observations, coverages, links, acts, missing, ledger)
