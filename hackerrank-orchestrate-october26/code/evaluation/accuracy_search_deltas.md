# Every changed target prediction in the rejected controls

The comparison baseline is the current production output, not hidden ground truth. Every changed case is listed below. All 518 case memberships were checked per strategy. Status changes are reported separately; matching statuses do not establish matching resources or citations.

All differences arise from the experimental tie-priority substitution and its downstream plan compilation. No observations, identity fields, policies or reference answers were supplied to the ordering rule. The rule does not establish ownership, so no control was promoted.

## latest_request_first

Changed targets: 3; status changes: 0. Sample fixes: case_23. Sample regressions: case_03, case_25, case_26.

### case_44

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 4 → 4 | resource_id | `analytics_5589` | `analytics_9406` |

### case_547

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_410` | `account_7015` |

### case_549

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|

Added step:

```json
{"evidence_id": "evidence_02", "operation": "VERIFY_RECORD_ANONYMIZED", "phase": "VERIFICATION", "resource_id": "analytics_1895", "state": "ANONYMIZED", "step_no": 4, "system_id": "analytics_platform"}
```

## earliest_request_first

Changed targets: 121; status changes: 0. Sample fixes: none. Sample regressions: case_25, case_26, case_27, case_28, case_29.

### case_47

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_617` | `account_483` |

### case_48

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_483` | `account_617` |

### case_56

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_5715` | `account_9862` |

### case_57

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 4 → 4 | resource_id | `analytics_2572` | `analytics_8858` |

### case_58

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_9862` | `account_5715` |
| 3 → 3 | resource_id | `analytics_8858` | `analytics_2572` |

### case_59

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_631` | `account_5661` |

### case_60

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_5661` | `account_631` |

### case_74

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_1495` | `account_9051` |

### case_75

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_9051` | `account_1495` |

### case_95

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 9 → 9 | resource_id | `account_5815` | `account_4176` |

### case_96

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_4176` | `account_5815` |

### case_98

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_7927` | `account_9511` |

### case_100

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_9511` | `account_7927` |

### case_104

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 9 → 9 | resource_id | `account_8804` | `account_4514` |

### case_106

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_4514` | `account_8804` |

### case_107

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_687` | `account_7510` |
| 3 → 3 | resource_id | `analytics_2777` | `analytics_5001` |

### case_108

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_5001` | `analytics_2777` |

### case_109

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_7510` | `account_687` |

### case_110

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_7578` | `account_2259` |

### case_111

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_800` | `analytics_9875` |

### case_112

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_2259` | `account_7578` |
| 4 → 4 | resource_id | `analytics_9875` | `analytics_800` |

### case_126

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_1402` | `analytics_7150` |

### case_127

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_7150` | `analytics_1402` |

### case_143

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_2900` | `account_5572` |

### case_145

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_5572` | `account_2900` |

### case_146

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_5023` | `account_7864` |

### case_148

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_7864` | `account_5023` |

### case_150

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_7254` | `analytics_1626` |

### case_151

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 4 → 4 | resource_id | `analytics_1626` | `analytics_7254` |

### case_155

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_1992` | `account_2154` |
| 4 → 4 | resource_id | `analytics_7372` | `analytics_8425` |

### case_157

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_2154` | `account_1992` |
| 3 → 3 | resource_id | `analytics_8425` | `analytics_7372` |

### case_185

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_9579` | `account_3878` |

### case_186

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_3878` | `account_9579` |

### case_191

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_6608` | `account_9317` |
| 1 → 1 | evidence_id | `evidence_20` | `evidence_83` |

### case_192

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 9 → 9 | resource_id | `account_9317` | `account_6608` |

### case_195

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_5166` | `analytics_3454` |

### case_196

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_3454` | `analytics_5166` |

### case_203

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_2399` | `account_6726` |

### case_205

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_6726` | `account_2399` |

### case_207

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_5678` | `account_3685` |

### case_208

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_3685` | `account_5678` |

### case_218

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_257` | `analytics_7004` |

### case_219

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_7004` | `analytics_257` |

### case_224

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_7605` | `account_392` |

### case_225

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_2501` | `analytics_8127` |

### case_226

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_392` | `account_7605` |
| 1 → 1 | evidence_id | `evidence_80` | `evidence_24` |
| 3 → 3 | resource_id | `analytics_8127` | `analytics_2501` |

### case_227

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_5549` | `account_7146` |

### case_229

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_7146` | `account_5549` |

### case_230

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_8165` | `account_8936` |

### case_232

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_8936` | `account_8165` |

### case_233

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 4 → 4 | resource_id | `analytics_6723` | `analytics_8565` |

### case_235

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 4 → 4 | resource_id | `analytics_8565` | `analytics_6723` |

### case_243

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_7650` | `account_4264` |
| 3 → 3 | resource_id | `analytics_9166` | `analytics_5891` |

### case_244

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_4264` | `account_7650` |
| 3 → 3 | resource_id | `analytics_5891` | `analytics_9166` |

### case_245

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_2481` | `account_1264` |

### case_246

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_1264` | `account_2481` |

### case_251

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_4643` | `account_7518` |

### case_252

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_7518` | `account_4643` |

### case_257

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_7942` | `account_3601` |

### case_258

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_3601` | `account_7942` |

### case_275

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_2352` | `account_731` |

### case_276

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_5923` | `analytics_6191` |

### case_277

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_731` | `account_2352` |
| 1 → 1 | evidence_id | `evidence_77` | `evidence_29` |
| 4 → 4 | resource_id | `analytics_6191` | `analytics_5923` |

### case_278

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 9 → 9 | resource_id | `account_6306` | `account_4664` |

### case_279

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_4664` | `account_6306` |

### case_293

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_9091` | `account_8353` |

### case_294

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_061` | `analytics_7575` |

### case_295

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_8353` | `account_9091` |
| 3 → 3 | resource_id | `analytics_7575` | `analytics_061` |

### case_297

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_6023` | `account_4880` |

### case_298

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_4880` | `account_6023` |

### case_299

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_7249` | `account_9993` |

### case_301

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_9993` | `account_7249` |

### case_303

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_7907` | `account_4771` |

### case_304

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_4771` | `account_7907` |

### case_308

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 4 → 4 | resource_id | `analytics_096` | `analytics_3678` |

### case_309

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_3678` | `analytics_096` |

### case_326

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 4 → 4 | resource_id | `analytics_9681` | `analytics_2072` |

### case_327

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_2072` | `analytics_9681` |

### case_345

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_8834` | `account_5214` |
| 3 → 3 | resource_id | `analytics_3990` | `analytics_7102` |

### case_346

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_5214` | `account_8834` |
| 3 → 3 | resource_id | `analytics_7102` | `analytics_3990` |

### case_347

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_3372` | `account_9881` |

### case_349

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_9881` | `account_3372` |

### case_359

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_6445` | `account_7118` |

### case_361

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_7118` | `account_6445` |

### case_374

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_5779` | `analytics_9394` |

### case_375

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_9394` | `analytics_5779` |

### case_395

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_3492` | `account_2464` |

### case_397

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_2464` | `account_3492` |

### case_398

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_2138` | `account_1140` |

### case_399

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_1140` | `account_2138` |

### case_404

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 9 → 9 | resource_id | `account_1759` | `account_8997` |

### case_406

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_8997` | `account_1759` |

### case_408

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_5754` | `account_7174` |
| 3 → 3 | resource_id | `analytics_8973` | `analytics_542` |

### case_409

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_7174` | `account_5754` |
| 3 → 3 | resource_id | `analytics_542` | `analytics_8973` |

### case_410

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_163` | `account_8985` |

### case_412

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_8985` | `account_163` |

### case_423

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_3845` | `analytics_6249` |

### case_424

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_6249` | `analytics_3845` |

### case_425

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 9 → 9 | resource_id | `account_1576` | `account_9633` |

### case_426

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_9633` | `account_1576` |

### case_443

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_4042` | `account_1776` |

### case_444

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_1776` | `account_4042` |

### case_447

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_7340` | `account_6635` |

### case_448

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_6635` | `account_7340` |

### case_455

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_6373` | `account_2761` |

### case_456

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_6750` | `analytics_1126` |

### case_457

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_2761` | `account_6373` |
| 3 → 3 | resource_id | `analytics_1126` | `analytics_6750` |

### case_480

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_9449` | `account_2465` |

### case_481

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_2465` | `account_9449` |

### case_504

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_8136` | `account_7244` |

### case_505

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_7244` | `account_8136` |

### case_527

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 9 → 9 | resource_id | `account_3693` | `account_4063` |

### case_529

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 5 → 5 | resource_id | `account_4063` | `account_3693` |

### case_530

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `analytics_3744` | `analytics_893` |

### case_532

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 4 → 4 | resource_id | `analytics_893` | `analytics_3744` |

### case_543

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_8931` | `account_7320` |

### case_544

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_7320` | `account_8931` |

### case_547

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_410` | `account_9155` |

### case_548

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_9155` | `account_410` |

### case_549

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 1 → 1 | resource_id | `account_4842` | `account_7225` |

### case_550

Status: INCOMPLETE → INCOMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 3 → 3 | resource_id | `account_7225` | `account_4842` |

## stable_subject_order

Changed targets: 1; status changes: 0. Sample fixes: none. Sample regressions: case_03.

### case_44

Status: COMPLETE → COMPLETE. Relative order changed: False.

| Matched position (before → after) | Field | Before | After |
|---|---|---|---|
| 4 → 4 | resource_id | `analytics_5589` | `analytics_9406` |
