"""Safety boundaries for evaluation-only assignment experiments."""
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation import assignment_experiment as experiment


def test_corrupt_prediction_is_rejected_before_reference_access(tmp_path):
    (tmp_path / 'source').mkdir()
    content = experiment.encode_rows([('case_synthetic', 'NOT_APPLICABLE', '[]')])
    (tmp_path / 'target.csv').write_bytes(content + b'corrupt')
    (tmp_path / 'all.csv').write_bytes(content)
    manifest = {'source_sha256': {}, 'candidates': [dict(outcome='produced', strategy='baseline',
        target_file='target.csv', all_file='all.csv', target_sha256=experiment.digest(content),
        all_sha256=experiment.digest(content))]}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    with patch('evaluation.score.load_answers') as reference_reader:
        with pytest.raises(ValueError, match='Frozen predictions changed'):
            experiment.compare(tmp_path / 'data', tmp_path)
        reference_reader.assert_not_called()


def test_frozen_source_cannot_escape_its_snapshot_directory(tmp_path):
    (tmp_path / 'source').mkdir()
    manifest = {'source_sha256': {'../../outside.py': hashlib.sha256(b'synthetic').hexdigest()}, 'candidates': []}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    with patch('evaluation.score.load_answers') as reference_reader:
        with pytest.raises(ValueError, match='Frozen source changed'):
            experiment.compare(tmp_path / 'data', tmp_path)
        reference_reader.assert_not_called()


def test_failed_controls_restore_production_function_and_reuse_one_index(tmp_path):
    request = dict(case_id='case_synthetic', requested_at='2026-01-01T00:00:00Z')
    original = experiment.workflow._number
    class FakeTools:
        indexes = 0
        investigations = 0
        def load_inputs(self, _):
            return SimpleNamespace(requests=(request,))
        def index_evidence(self, _):
            self.indexes += 1
            return object()
        def investigate(self, *_):
            self.investigations += 1
            if self.investigations > 1:
                assert experiment.workflow._number is not original
                raise RuntimeError('synthetic control failure')
            return {'case_synthetic': SimpleNamespace(status='NOT_APPLICABLE', subject=SimpleNamespace(user_id='user_9001'))}
        def compile_plan(self, *_):
            return [('case_synthetic', 'NOT_APPLICABLE', '[]')]
        def validate(self, *_):
            return [], 1
    tools = FakeTools()
    with patch.object(experiment, 'AuditTools', return_value=tools), patch.object(experiment, 'steps_for', return_value=[]):
        result = experiment.predict(tmp_path / 'data', tmp_path / 'run', repeats=1)
    assert experiment.workflow._number is original
    assert tools.indexes == 1
    assert [r['outcome'] for r in result['candidates']] == ['produced', 'failed', 'failed', 'failed']
