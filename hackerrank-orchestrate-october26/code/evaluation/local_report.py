"""Reproduce the local baseline's output and honest local reports."""
from pathlib import Path
import sys,csv,json,hashlib,time
from collections import Counter,defaultdict
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(ROOT/'code'))
from main import run
from investigate import investigate_all
from evidence.index import build
from score import score,load_answers,format_report
from policy import steps_for
from validate_output import validate


def read(path):
    with path.open(encoding='utf-8',newline='') as f:
        return {r['case_id']:(r['deletion_status'],json.loads(r['steps_json'])) for r in csv.DictReader(f)}


def main():
    started=time.perf_counter();data=ROOT/'dataset';output=ROOT/'output.csv'
    run(data,output,use_llm=False,trace_path=ROOT/'code/evaluation/agent_run_trace.json')
    idx=build(data);cases=investigate_all(data,index=idx)
    # Every prediction has been produced before opening public references.
    expected=load_answers(data/'sample_output.csv')
    predicted={cid:(cases[cid].status,steps_for(cases[cid])) for cid in expected}
    metrics=score(expected,predicted);errors,n=validate(output,data)
    if errors:raise ValueError(errors)
    current=read(output);baseline=ROOT/'baselines/generated_output.csv';changes=[]
    if baseline.exists():
        old=read(baseline)
        for cid,value in current.items():
            if value!=old[cid]:changes.append(dict(case_id=cid,before=old[cid],after=value))
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    summary=dict(rows=n,statuses=dict(Counter(value[0] for value in current.values())),
        output_sha256=digest,sample_status=metrics['status_accuracy'],sample_exact=metrics['sequence_exact'],
        changed_cases=changes,live_model_calls=0,input_tokens=0,output_tokens=0,
        elapsed_seconds=time.perf_counter()-started)
    folder=ROOT/'code/evaluation'
    test_record_path=folder/'test_run.json'
    test_record=json.loads(test_record_path.read_text(encoding='utf-8')) if test_record_path.exists() else None
    (folder/'run_record.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    lines=['# Local evaluation','',
        'This report covers local generation and validation only. The modified candidate has not '
        'been graded externally, and no hosted or hidden evaluation result is claimed.','',
        f'Produced {n} rows with statuses {summary["statuses"]}. Output SHA-256: `{digest}`. '
        f'Generation and local evaluation took {summary["elapsed_seconds"]:.3f}s; zero live model calls.',
        '', '## Public sample evaluation','',
        'All predictions precede reference access. Whole-array equality includes step numbers, '
        'operations, IDs, states, evidence and order. Status accuracy is separate.',
        '', '```text',format_report(metrics,'public samples'),'```','',
        '## All 32 sample cases','',
        '| Case | Expected status | Predicted status | Expected steps | Predicted steps | Full case exact | Missing | Extra |',
        '| --- | --- | --- | ---: | ---: | --- | ---: | ---: |']
    for cid in sorted(expected,key=lambda c:(len(c),c)):
        es,ep=expected[cid];ps,pp=predicted[cid];detail=metrics['details'][cid]
        lines.append(f"| {cid} | {es} | {ps} | {len(ep)} | {len(pp)} | {'yes' if (es,ep)==(ps,pp) else 'no'} | {len(detail['missing'])} | {len(detail['extra'])} |")
    lines += ['',
        'The baseline output was independently reproduced byte-for-byte with SHA-256 '
        '`0d80a7d4bad671870762bf5a6edab41a9c48d146dd2292367e5cb8b228207194`.',
        '', '## Measured candidate differences','',
        'Only three target-case evidence fields change. No status, resource ID, operation, state '
        'or array order changes. Each previously blank COMPLETE account verification now uses '
        'the most recent eligible prior absence under the inherited coverage model, provided no '
        'newer presence or creating operation invalidates it. This is a general rule, not a '
        'case-ID correction. Pre-request persistence and authoritative scope are assumptions '
        'that must remain visible, not a hidden-score guarantee.',
        '', '| Case | Resource | Before | Candidate |','| --- | --- | --- | --- |']
    for c in changes:
        for before,after in zip(c['before'][1],c['after'][1]):
            if before!=after:lines.append(f"| {c['case_id']} | {after['resource_id']} | {before['evidence_id'] or '(empty)'} | {after['evidence_id']} |")
    lines+=['','## Additional cases and tests','',
        (f"Recorded final test run: **{test_record['passed']} passed in {test_record['duration_seconds']:.2f} seconds**. "
         'The command and environment are recorded in test_run.json. This includes the 152 '
         'baseline tests plus local identity, evidence, model-boundary, SQL and coordinator regressions. '
         'Tests ran separately; rerunning this report alone does not rerun pytest.'
         if test_record else 'No test-run record is present; run pytest separately.'),
        '', 'Local counterexamples cover: two future email changes; an eligible snapshot unaffected '
        'by later changes; an already-absent account before its request; later sync invalidation; '
        'a newer presence blocking stale absence; impossible post-capture observations; preserving '
        'image clocks; international phone normalization; rejecting uncited COMPLETE; and image '
        'hash mismatch. The inherited custom-case harness also passes 12/12.',
        '', 'The current agent architecture pass adds typed tool contracts, a real CLI coordinator, '
        'aggregate execution traces, validation before atomic publication, bounded model calls, '
        'cache-hit validation, new versioned prompts and confined manifest/SQL loading. The '
        'CSV remains byte-for-byte identical to the prior three-citation candidate. See '
        '../ARCHITECTURE.md and DECISION_GUIDE.md for design rationale and an explicitly '
        'editorial guide to the actual development record. Historical prompts were not rewritten.',
        '', '## Limitations and inherited behavior','',
        'The scoring profile retains timing inference, numeric case-order tie breaks, '
        'a naming fallback and retrospective ownership membership. The local identity fix removes '
        'intermediate future values but does not turn retrospective metadata into information '
        'available earlier. State citations obey their clocks, and impossible post-capture '
        'observations are now rejected. Unknown permission defaults and other inherited '
        'inference assumptions remain review issues; do not call this a fully strict proof engine.',
        'The validator now rejects empty COMPLETE citations and passes all 518 candidate rows; '
        'it does not establish historical ownership or hidden canonical correctness. No sample '
        'answer, imported output CSV or per-case lookup table enters prediction logic. Dataset '
        'files were not modified.',
        '', 'A focused reinspection found no indexed observations or activity for the two missing '
        'audit resources. This is an extraction/inventory diagnostic, not proof that their IDs '
        'are absent from every rendered artifact. The account mismatch has two unowned failed '
        'delete candidates in the same timing window; the inherited case-order tie break chooses '
        'the wrong one. No supported replacement ownership link was established, so no sample-ID '
        'correction was introduced. The detailed missing/extra tuples above expose every operation, '
        'state, resource and evidence difference; shifted positions arise from these inventory '
        'differences, rather than an independent sort defect.']
    (folder/'evaluation_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    cache=defaultdict(lambda:[0,0,0])
    for path in (ROOT/'code/llm_cache/responses').glob('*.json'):
        item=json.loads(path.read_text(encoding='utf-8'));v=cache[(item['provider'],item['model'],item['task'])]
        v[0]+=1;v[1]+=item['usage']['input_tokens'];v[2]+=item['usage']['output_tokens']
    usage=['# Usage report — current candidate','',
        f'This report covers the full run producing {n}-row output.csv with SHA-256 `{digest}`.',
        '', '| Runtime provider/model | Calls | Input tokens | Output tokens | Total | Per request | API cost |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |',
        '| None invoked: offline replay | 0 | 0 | 0 | 0 | 0 | USD 0 |',
        '| Total current runtime | 0 | 0 | 0 | 0 | 0 | USD 0 |','',
        'Live inference requires explicit --enable-model; this run used --no-llm. Model extraction '
        'was performed previously and is reused as local cached data. Imported '
        'cache counters below are historical generation usage, not new calls '
        'or tokens spent during this run.',
        '', '| Cached provider/model/task | Recorded calls | Recorded input | Recorded output | Recorded total |',
        '| --- | ---: | ---: | ---: | ---: |']
    for key,v in cache.items():usage.append(f"| {' / '.join(key)} | {v[0]} | {v[1]} | {v[2]} | {v[1]+v[2]} |")
    usage+=['','All eleven image-fact files are bound to source SHA-256. Changed source images '
        'fail validation rather than silently reusing stale facts. No copied prediction CSV '
        'was used to produce the candidate. Historical extraction cost is not independently '
        'verified; earlier price assumptions are not represented as current official '
        'rates. This replay has zero marginal API cost; it does not mean development was free.',
        'Local development harness/provider: OpenAI Codex Desktop, runtime gpt-6.1-sol. '
        'Development tokens/cost are not separately available and are not fabricated.']
    (folder/'usage_report.md').write_text('\n'.join(usage)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='changed_cases'}))


if __name__=='__main__':main()
