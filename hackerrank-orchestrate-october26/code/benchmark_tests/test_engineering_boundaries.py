"""Independent regressions for orchestration and publication failure boundaries."""
from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_tools import AuditTools
from benchmark_agent import AuditAgent, OutputValidationError, RunState, RunTrace, ToolContractError
from test_agent_workflow import FixtureTools
from audit_artifacts import atomic_json


def test_out_of_order_publication_never_invokes_the_action():
    called = []
    agent = AuditAgent(FixtureTools())
    with pytest.raises(ToolContractError, match='out of order'):
        agent._call('publish', lambda: called.append(True))
    assert not called
    assert agent.trace.state is RunState.FAILED


def test_extra_tool_capabilities_are_rejected_before_execution(tmp_path):
    tools = FixtureTools()
    tools.contracts = dict(tools.contracts)
    tools.contracts['load_inputs'] = replace(tools.contracts['load_inputs'], effects=('read_dataset', 'write_output'))
    tools.load_inputs = lambda _: pytest.fail('Unauthorized tool ran')
    agent = AuditAgent(tools)
    with pytest.raises(ToolContractError, match='capabilities'):
        agent.run(tmp_path / 'dataset', tmp_path / 'out.csv')
    assert agent.trace.events[0].effects == ('read_dataset',)


def test_validator_cannot_mutate_a_candidate_and_approve_it(tmp_path):
    class MutatingValidator(FixtureTools):
        def validate(self, candidate, data_dir):
            candidate.write_bytes(b'unvalidated bytes')
            return [], 1
    output = tmp_path / 'out.csv'
    output.write_bytes(b'previous validated output')
    agent = AuditAgent(MutatingValidator())
    with pytest.raises(OutputValidationError, match='modified'):
        agent.run(tmp_path / 'dataset', output)
    assert output.read_bytes() == b'previous validated output'
    assert agent.trace.events[-1].tool == 'validate'
    assert agent.trace.events[-1].outcome == 'failed'


def test_candidate_changed_after_validation_cannot_publish(tmp_path):
    class MutatedBeforeCommit(AuditAgent):
        def _publish(self, candidate, destination):
            candidate.write_bytes(b'changed after approval')
            return super()._publish(candidate, destination)
    output = tmp_path / 'out.csv'
    output.write_bytes(b'previous validated output')
    with pytest.raises(OutputValidationError, match='unchanged validated'):
        MutatedBeforeCommit(FixtureTools()).run(tmp_path / 'dataset', output)
    assert output.read_bytes() == b'previous validated output'


@pytest.mark.parametrize('result', [(None, 1), ([], True), ((), 1), ([], '1')])
def test_malformed_validator_result_never_approves_publication(tmp_path, result):
    tools = FixtureTools()
    tools.validate = lambda *_: result
    with pytest.raises(ToolContractError, match='Validator'):
        AuditAgent(tools).run(tmp_path / 'dataset', tmp_path / 'out.csv')
    assert not (tmp_path / 'out.csv').exists()


def test_ledger_export_failure_preserves_the_primary_error(tmp_path):
    class BrokenLedger:
        def summary(self): return {}
        def write(self, _): raise OSError('sensitive diagnostic failure')
    class OriginalFailure(ValueError):
        ledger = BrokenLedger()
    original = OriginalFailure('sensitive source failure')
    agent = AuditAgent(FixtureTools(index_error=original))
    trace = tmp_path / 'trace.json'
    with pytest.raises(OriginalFailure) as error:
        agent.run(tmp_path / 'dataset', tmp_path / 'out.csv', trace, tmp_path / 'ledger.json')
    assert error.value is original
    assert agent.trace.failure_type == 'OriginalFailure'
    assert agent.trace.diagnostic_errors == ['ledger_write_failed']
    assert 'sensitive' not in trace.read_text()


def test_unwritable_requested_trace_blocks_commit_before_output_changes(tmp_path, monkeypatch):
    def fail(*_): raise OSError('sensitive trace failure')
    monkeypatch.setattr(RunTrace, 'write', fail)
    output = tmp_path / 'out.csv'
    output.write_bytes(b'previous validated output')
    agent = AuditAgent(FixtureTools())
    with pytest.raises(OSError):
        agent.run(tmp_path / 'dataset', output, tmp_path / 'trace.json')
    assert output.read_bytes() == b'previous validated output'
    assert not agent.trace.published
    assert not any(e.tool == 'publish' for e in agent.trace.events)


def test_trace_finalization_failure_does_not_misreport_committed_csv(tmp_path, monkeypatch):
    original = RunTrace.write
    calls = []
    def fail_second(self, path):
        calls.append(True)
        if len(calls) == 2: raise OSError('sensitive finalization failure')
        return original(self, path)
    monkeypatch.setattr(RunTrace, 'write', fail_second)
    agent = AuditAgent(FixtureTools())
    rows = agent.run(tmp_path / 'dataset', tmp_path / 'out.csv', tmp_path / 'trace.json')
    assert rows and (tmp_path / 'out.csv').exists()
    assert agent.trace.state is RunState.PUBLISHED and agent.trace.published
    assert agent.trace.diagnostic_errors == ['trace_write_failed']


def test_missing_investigations_are_recorded_at_the_correct_stage(tmp_path):
    tools = FixtureTools()
    tools.investigate = lambda *_: {}
    agent = AuditAgent(tools)
    with pytest.raises(ToolContractError, match='case membership'):
        agent.run(tmp_path / 'dataset', tmp_path / 'out.csv')
    assert agent.trace.events[-1].tool == 'investigate'
    assert agent.trace.events[-1].outcome == 'failed'


def test_request_snapshots_are_read_only(tmp_path):
    (tmp_path / 'deletion_requests.csv').write_text('case_id,email,requested_at,reported_status,reported_at,audit_at,request_text\n'
        'synthetic,person@example.test,2026-01-01T00:00:00Z,COMPLETE,2026-01-01T00:00:00Z,2026-01-02T00:00:00Z,Please delete my account.\n')
    inputs = AuditTools().load_inputs(tmp_path)
    with pytest.raises(TypeError):
        inputs.requests[0]['email'] = 'changed@example.test'


def test_backups_cannot_be_written_into_the_read_only_dataset(tmp_path):
    with pytest.raises(ValueError, match='Backup'):
        AuditAgent(FixtureTools(), backup_dir=tmp_path / 'dataset/backups').run(tmp_path / 'dataset', tmp_path / 'out.csv')


def test_cli_defaults_to_offline_and_requires_consistent_options(monkeypatch):
    import main
    calls = []
    monkeypatch.setattr(main, 'run', lambda *args, **kwargs: calls.append(kwargs))
    monkeypatch.setattr(sys, 'argv', ['main.py'])
    main.main()
    assert calls[-1]['use_llm'] is False
    monkeypatch.setattr(sys, 'argv', ['main.py', '--enable-model'])
    main.main()
    assert calls[-1]['use_llm'] is True
    monkeypatch.setattr(sys, 'argv', ['main.py', '--enable-model', '--no-llm'])
    with pytest.raises(SystemExit): main.main()


def test_atomic_diagnostic_failure_preserves_previous_json(tmp_path, monkeypatch):
    path = tmp_path / 'trace.json'
    path.write_text('{"previous":true}', encoding='utf-8')
    def fail(*_): raise OSError('synthetic replacement failure')
    monkeypatch.setattr('audit_artifacts.os.replace', fail)
    with pytest.raises(OSError): atomic_json(path, {'new': True})
    assert json.loads(path.read_text()) == {'previous': True}
    assert not list(tmp_path.glob('.json-*'))


def test_candidate_cleanup_failure_does_not_hide_validation_failure(tmp_path, monkeypatch):
    original = Path.unlink
    def fail_candidate(self, *args, **kwargs):
        if self.name.startswith('.audit-'): raise PermissionError('synthetic cleanup failure')
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Path, 'unlink', fail_candidate)
    agent = AuditAgent(FixtureTools(errors=['invalid']))
    with pytest.raises(OutputValidationError):
        agent.run(tmp_path / 'dataset', tmp_path / 'out.csv')
    assert agent.trace.failure_type == 'OutputValidationError'
    assert agent.trace.diagnostic_errors == ['candidate_cleanup_failed']


def test_rejected_reused_run_does_not_retain_previous_publication_approval(tmp_path):
    agent = AuditAgent(FixtureTools(), backup_dir=tmp_path / 'backups')
    agent.run(tmp_path / 'dataset', tmp_path / 'first.csv')
    assert agent.trace.published
    with pytest.raises(ValueError, match='read-only dataset'):
        agent.run(tmp_path / 'dataset', tmp_path / 'dataset/out.csv')
    assert not agent.trace.published and agent._validated is None
    assert not agent.trace.events
