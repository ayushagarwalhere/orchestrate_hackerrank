# Public sample comparison

Predictions were frozen before this comparison read the reference file. Earlier conversation work inspected public examples, so this is not a blind evaluation.

Status accuracy: 11/32 (34.38%).
Full-case exact accuracy: 1/32 (3.12%).
Prediction coverage: 11/32; execution failures remain failures, not invented statuses.

Exact-step precision/recall: 67.24% / 20.21%. Field accuracy: 28.65% (missing steps contribute zero correct fields). Exact sequences: 1/32.

| Case | Predicted | Reference | Status | Full case | Root failure / deltas |
|---|---|---|---|---|---|
| case_01 | NO PREDICTION | COMPLETE | False | False | investigate:missing_ownership |
| case_02 | NO PREDICTION | COMPLETE | False | False | investigate:request_intent |
| case_03 | COMPLETE | COMPLETE | True | False | missing=1, extra=0, field errors=0, order=False |
| case_04 | NO PREDICTION | COMPLETE | False | False | investigate:missing_ownership |
| case_05 | INCOMPLETE | INCOMPLETE | True | True | missing=0, extra=0, field errors=0, order=False |
| case_06 | INCOMPLETE | INCOMPLETE | True | False | missing=1, extra=0, field errors=1, order=False |
| case_07 | NO PREDICTION | INCOMPLETE | False | False | investigate:missing_state |
| case_08 | NO PREDICTION | INCOMPLETE | False | False | investigate:request_intent |
| case_09 | INCOMPLETE | INCOMPLETE | True | False | missing=2, extra=0, field errors=1, order=False |
| case_10 | NO PREDICTION | INCOMPLETE | False | False | investigate:request_intent |
| case_11 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_12 | NO PREDICTION | INCOMPLETE | False | False | investigate:request_intent |
| case_13 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_14 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_15 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_16 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_17 | NO PREDICTION | INCOMPLETE | False | False | investigate:missing_state |
| case_18 | INCOMPLETE | INCOMPLETE | True | False | missing=2, extra=0, field errors=4, order=False |
| case_19 | NO PREDICTION | INCOMPLETE | False | False | investigate:request_intent |
| case_20 | INCOMPLETE | INCOMPLETE | True | False | missing=2, extra=0, field errors=2, order=False |
| case_21 | COMPLETE | COMPLETE | True | False | missing=2, extra=0, field errors=1, order=False |
| case_22 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_23 | INCOMPLETE | INCOMPLETE | True | False | missing=2, extra=0, field errors=2, order=False |
| case_24 | INCOMPLETE | INCOMPLETE | True | False | missing=1, extra=0, field errors=0, order=False |
| case_25 | NO PREDICTION | COMPLETE | False | False | investigate:request_intent |
| case_26 | NO PREDICTION | COMPLETE | False | False | investigate:request_intent |
| case_27 | NO PREDICTION | COMPLETE | False | False | investigate:request_intent |
| case_28 | COMPLETE | COMPLETE | True | False | missing=2, extra=0, field errors=4, order=False |
| case_29 | NO PREDICTION | INCOMPLETE | False | False | investigate:request_intent |
| case_30 | INCOMPLETE | INCOMPLETE | True | False | missing=2, extra=0, field errors=4, order=False |
| case_31 | NO PREDICTION | COMPLETE | False | False | investigate:request_intent |
| case_32 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |

## case_01

```json
{
  "case_id": "case_01",
  "expected_status": "COMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_01",
    "failure_type": "investigation_unresolved",
    "reason": "missing_ownership",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "evidence_id": "evidence_54",
      "operation": "VERIFY_RECORD_ABSENT",
      "phase": "VERIFICATION",
      "resource_id": "account_001",
      "state": "ABSENT",
      "step_no": 1,
      "system_id": "account_service"
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 1,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 7,
  "sequence_exact": false
}
```

## case_02

```json
{
  "case_id": "case_02",
  "expected_status": "COMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_02",
    "failure_type": "investigation_unresolved",
    "reason": "request_intent",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "evidence_id": "evidence_54",
      "operation": "VERIFY_RECORD_ABSENT",
      "phase": "VERIFICATION",
      "resource_id": "account_002",
      "state": "ABSENT",
      "step_no": 1,
      "system_id": "account_service"
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 1,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 7,
  "sequence_exact": false
}
```

## case_03

```json
{
  "case_id": "case_03",
  "expected_status": "COMPLETE",
  "actual_status": "COMPLETE",
  "status_correct": true,
  "full_case_exact": false,
  "failure": null,
  "missing_steps": [
    {
      "step_no": 3,
      "phase": "VERIFICATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_9406",
      "operation": "VERIFY_RECORD_ANONYMIZED",
      "state": "ANONYMIZED",
      "evidence_id": "evidence_94"
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 3,
  "actual_steps": 2,
  "exact_steps": 2,
  "correct_fields": 14,
  "expected_fields": 21,
  "sequence_exact": false
}
```

## case_04

```json
{
  "case_id": "case_04",
  "expected_status": "COMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_04",
    "failure_type": "investigation_unresolved",
    "reason": "missing_ownership",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "evidence_id": "evidence_54",
      "operation": "VERIFY_RECORD_ABSENT",
      "phase": "VERIFICATION",
      "resource_id": "account_004",
      "state": "ABSENT",
      "step_no": 1,
      "system_id": "account_service"
    },
    {
      "evidence_id": "evidence_56",
      "operation": "VERIFY_RECORD_ANONYMIZED",
      "phase": "VERIFICATION",
      "resource_id": "analytics_901",
      "state": "ANONYMIZED",
      "step_no": 2,
      "system_id": "analytics_platform"
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 2,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 14,
  "sequence_exact": false
}
```

## case_06

```json
{
  "case_id": "case_06",
  "expected_status": "INCOMPLETE",
  "actual_status": "INCOMPLETE",
  "status_correct": true,
  "full_case_exact": false,
  "failure": null,
  "missing_steps": [
    {
      "evidence_id": "",
      "operation": "VERIFY_RECORD_ABSENT",
      "phase": "VERIFICATION",
      "resource_id": "account_006",
      "state": "ABSENT",
      "step_no": 3,
      "system_id": "account_service"
    }
  ],
  "extra_steps": [],
  "field_errors": [
    {
      "expected_index": 4,
      "actual_index": 3,
      "fields": {
        "step_no": {
          "expected": 4,
          "actual": 3
        }
      }
    }
  ],
  "order_error": false,
  "expected_steps": 4,
  "actual_steps": 3,
  "exact_steps": 2,
  "correct_fields": 20,
  "expected_fields": 28,
  "sequence_exact": false
}
```

## case_07

```json
{
  "case_id": "case_07",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_07",
    "failure_type": "investigation_unresolved",
    "reason": "missing_state",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "evidence_id": "evidence_58",
      "operation": "REPORT_REMAINING_RECORD",
      "phase": "FINDING",
      "resource_id": "support_001",
      "state": "PRESENT",
      "step_no": 1,
      "system_id": "support_platform"
    },
    {
      "evidence_id": "",
      "operation": "DELETE_RECORD",
      "phase": "REMEDIATION",
      "resource_id": "support_001",
      "state": "ABSENT",
      "step_no": 2,
      "system_id": "support_platform"
    },
    {
      "evidence_id": "",
      "operation": "VERIFY_RECORD_ABSENT",
      "phase": "VERIFICATION",
      "resource_id": "account_007",
      "state": "ABSENT",
      "step_no": 3,
      "system_id": "account_service"
    },
    {
      "evidence_id": "",
      "operation": "VERIFY_RECORD_ABSENT",
      "phase": "VERIFICATION",
      "resource_id": "support_001",
      "state": "ABSENT",
      "step_no": 4,
      "system_id": "support_platform"
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 4,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 28,
  "sequence_exact": false
}
```

## case_08

```json
{
  "case_id": "case_08",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_08",
    "failure_type": "investigation_unresolved",
    "reason": "request_intent",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "evidence_id": "evidence_59",
      "operation": "REPORT_REMAINING_RECORD",
      "phase": "FINDING",
      "resource_id": "export_001",
      "state": "PRESENT",
      "step_no": 1,
      "system_id": "export_service"
    },
    {
      "evidence_id": "",
      "operation": "DELETE_RECORD",
      "phase": "REMEDIATION",
      "resource_id": "export_001",
      "state": "ABSENT",
      "step_no": 2,
      "system_id": "export_service"
    },
    {
      "evidence_id": "",
      "operation": "VERIFY_RECORD_ABSENT",
      "phase": "VERIFICATION",
      "resource_id": "account_008",
      "state": "ABSENT",
      "step_no": 3,
      "system_id": "account_service"
    },
    {
      "evidence_id": "",
      "operation": "VERIFY_RECORD_ABSENT",
      "phase": "VERIFICATION",
      "resource_id": "export_001",
      "state": "ABSENT",
      "step_no": 4,
      "system_id": "export_service"
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 4,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 28,
  "sequence_exact": false
}
```

## case_09

```json
{
  "case_id": "case_09",
  "expected_status": "INCOMPLETE",
  "actual_status": "INCOMPLETE",
  "status_correct": true,
  "full_case_exact": false,
  "failure": null,
  "missing_steps": [
    {
      "step_no": 3,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_3960",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 4,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_4902",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [
    {
      "expected_index": 5,
      "actual_index": 3,
      "fields": {
        "step_no": {
          "expected": 5,
          "actual": 3
        }
      }
    }
  ],
  "order_error": false,
  "expected_steps": 5,
  "actual_steps": 3,
  "exact_steps": 2,
  "correct_fields": 20,
  "expected_fields": 35,
  "sequence_exact": false
}
```

## case_10

```json
{
  "case_id": "case_10",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_10",
    "failure_type": "investigation_unresolved",
    "reason": "request_intent",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "evidence_id": "evidence_61",
      "operation": "REPORT_REMAINING_RECORD",
      "phase": "FINDING",
      "resource_id": "support_002",
      "state": "PRESENT",
      "step_no": 1,
      "system_id": "support_platform"
    },
    {
      "evidence_id": "",
      "operation": "DELETE_RECORD",
      "phase": "REMEDIATION",
      "resource_id": "support_002",
      "state": "ABSENT",
      "step_no": 2,
      "system_id": "support_platform"
    },
    {
      "evidence_id": "",
      "operation": "VERIFY_RECORD_ABSENT",
      "phase": "VERIFICATION",
      "resource_id": "account_010",
      "state": "ABSENT",
      "step_no": 3,
      "system_id": "account_service"
    },
    {
      "evidence_id": "",
      "operation": "VERIFY_RECORD_ABSENT",
      "phase": "VERIFICATION",
      "resource_id": "support_002",
      "state": "ABSENT",
      "step_no": 4,
      "system_id": "support_platform"
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 4,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 28,
  "sequence_exact": false
}
```

## case_11

```json
{
  "case_id": "case_11",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_11",
    "failure_type": "policy_unresolved",
    "reason": null,
    "stage": "compile_plan"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "FINDING",
      "system_id": "search_service",
      "resource_id": "search_052",
      "operation": "REPORT_REMAINING_RECORD",
      "state": "PRESENT",
      "evidence_id": "evidence_03"
    },
    {
      "step_no": 2,
      "phase": "FINDING",
      "system_id": "analytics_platform",
      "resource_id": "analytics_2034",
      "operation": "REPORT_EXPOSED_PII",
      "state": "PRESENT",
      "evidence_id": "evidence_03"
    },
    {
      "step_no": 3,
      "phase": "FINDING",
      "system_id": "support_platform",
      "resource_id": "support_864",
      "operation": "REPORT_EXPOSED_PII",
      "state": "PRESENT",
      "evidence_id": "evidence_03"
    },
    {
      "step_no": 4,
      "phase": "FINDING",
      "system_id": "integration_service",
      "resource_id": "data_flow_9522",
      "operation": "REPORT_ACTIVE_DATA_FLOW",
      "state": "ACTIVE",
      "evidence_id": "evidence_03"
    },
    {
      "step_no": 5,
      "phase": "REMEDIATION",
      "system_id": "integration_service",
      "resource_id": "data_flow_9522",
      "operation": "DISABLE_DATA_FLOW",
      "state": "DISABLED",
      "evidence_id": ""
    },
    {
      "step_no": 6,
      "phase": "REMEDIATION",
      "system_id": "search_service",
      "resource_id": "search_052",
      "operation": "DELETE_RECORD",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 7,
      "phase": "REMEDIATION",
      "system_id": "support_platform",
      "resource_id": "support_864",
      "operation": "REDACT_RECORD",
      "state": "REDACTED",
      "evidence_id": ""
    },
    {
      "step_no": 8,
      "phase": "REMEDIATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_2034",
      "operation": "ANONYMIZE_RECORD",
      "state": "ANONYMIZED",
      "evidence_id": ""
    },
    {
      "step_no": 9,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_4248",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 10,
      "phase": "VERIFICATION",
      "system_id": "search_service",
      "resource_id": "search_052",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 11,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_9394",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    },
    {
      "step_no": 12,
      "phase": "VERIFICATION",
      "system_id": "support_platform",
      "resource_id": "support_864",
      "operation": "VERIFY_RECORD_REDACTED",
      "state": "REDACTED",
      "evidence_id": ""
    },
    {
      "step_no": 13,
      "phase": "VERIFICATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_2034",
      "operation": "VERIFY_RECORD_ANONYMIZED",
      "state": "ANONYMIZED",
      "evidence_id": ""
    },
    {
      "step_no": 14,
      "phase": "VERIFICATION",
      "system_id": "integration_service",
      "resource_id": "data_flow_9522",
      "operation": "VERIFY_DATA_FLOW_DISABLED",
      "state": "DISABLED",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 14,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 98,
  "sequence_exact": false
}
```

## case_12

```json
{
  "case_id": "case_12",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_12",
    "failure_type": "investigation_unresolved",
    "reason": "request_intent",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "FINDING",
      "system_id": "analytics_platform",
      "resource_id": "analytics_9914",
      "operation": "REPORT_REMAINING_RECORD",
      "state": "PRESENT",
      "evidence_id": "evidence_01"
    },
    {
      "step_no": 2,
      "phase": "REMEDIATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_9914",
      "operation": "DELETE_RECORD",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 3,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_9797",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 4,
      "phase": "VERIFICATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_9914",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_2945",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 5,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 35,
  "sequence_exact": false
}
```

## case_13

```json
{
  "case_id": "case_13",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_13",
    "failure_type": "policy_unresolved",
    "reason": null,
    "stage": "compile_plan"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "FINDING",
      "system_id": "search_service",
      "resource_id": "search_1308",
      "operation": "REPORT_REMAINING_RECORD",
      "state": "PRESENT",
      "evidence_id": "evidence_03"
    },
    {
      "step_no": 2,
      "phase": "FINDING",
      "system_id": "support_platform",
      "resource_id": "support_4218",
      "operation": "REPORT_REMAINING_RECORD",
      "state": "PRESENT",
      "evidence_id": "evidence_03"
    },
    {
      "step_no": 3,
      "phase": "REMEDIATION",
      "system_id": "search_service",
      "resource_id": "search_1308",
      "operation": "DELETE_RECORD",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 4,
      "phase": "REMEDIATION",
      "system_id": "support_platform",
      "resource_id": "support_4218",
      "operation": "DELETE_RECORD",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_9335",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 6,
      "phase": "VERIFICATION",
      "system_id": "search_service",
      "resource_id": "search_1308",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 7,
      "phase": "VERIFICATION",
      "system_id": "support_platform",
      "resource_id": "support_4218",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 8,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_4816",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 8,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 56,
  "sequence_exact": false
}
```

## case_14

```json
{
  "case_id": "case_14",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_14",
    "failure_type": "policy_unresolved",
    "reason": null,
    "stage": "compile_plan"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "FINDING",
      "system_id": "backup_service",
      "resource_id": "backup_3870",
      "operation": "REPORT_RESTORE_RISK",
      "state": "ACTIVE",
      "evidence_id": "evidence_03"
    },
    {
      "step_no": 2,
      "phase": "REMEDIATION",
      "system_id": "backup_service",
      "resource_id": "backup_3870",
      "operation": "BLOCK_RESTORE",
      "state": "BLOCKED",
      "evidence_id": ""
    },
    {
      "step_no": 3,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_3677",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 4,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_987",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    },
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "backup_service",
      "resource_id": "backup_3870",
      "operation": "VERIFY_RESTORE_BLOCKED",
      "state": "BLOCKED",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 5,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 35,
  "sequence_exact": false
}
```

## case_15

```json
{
  "case_id": "case_15",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_15",
    "failure_type": "policy_unresolved",
    "reason": null,
    "stage": "compile_plan"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "FINDING",
      "system_id": "integration_service",
      "resource_id": "data_flow_9846",
      "operation": "REPORT_ACTIVE_DATA_FLOW",
      "state": "ACTIVE",
      "evidence_id": "evidence_01"
    },
    {
      "step_no": 2,
      "phase": "REMEDIATION",
      "system_id": "integration_service",
      "resource_id": "data_flow_9846",
      "operation": "DISABLE_DATA_FLOW",
      "state": "DISABLED",
      "evidence_id": ""
    },
    {
      "step_no": 3,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_4745",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 4,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_1596",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    },
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "integration_service",
      "resource_id": "data_flow_9846",
      "operation": "VERIFY_DATA_FLOW_DISABLED",
      "state": "DISABLED",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 5,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 35,
  "sequence_exact": false
}
```

## case_16

```json
{
  "case_id": "case_16",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_16",
    "failure_type": "policy_unresolved",
    "reason": null,
    "stage": "compile_plan"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "FINDING",
      "system_id": "account_service",
      "resource_id": "account_994",
      "operation": "REPORT_REMAINING_RECORD",
      "state": "PRESENT",
      "evidence_id": "evidence_05"
    },
    {
      "step_no": 2,
      "phase": "FINDING",
      "system_id": "search_service",
      "resource_id": "search_1007",
      "operation": "REPORT_REMAINING_RECORD",
      "state": "PRESENT",
      "evidence_id": "evidence_05"
    },
    {
      "step_no": 3,
      "phase": "REMEDIATION",
      "system_id": "account_service",
      "resource_id": "account_994",
      "operation": "DELETE_RECORD",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 4,
      "phase": "REMEDIATION",
      "system_id": "search_service",
      "resource_id": "search_1007",
      "operation": "DELETE_RECORD",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_994",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 6,
      "phase": "VERIFICATION",
      "system_id": "search_service",
      "resource_id": "search_1007",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 7,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_9528",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 7,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 49,
  "sequence_exact": false
}
```

## case_17

```json
{
  "case_id": "case_17",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_17",
    "failure_type": "investigation_unresolved",
    "reason": "missing_state",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "FINDING",
      "system_id": "backup_service",
      "resource_id": "backup_3245",
      "operation": "REPORT_RESTORE_RISK",
      "state": "ACTIVE",
      "evidence_id": "evidence_01"
    },
    {
      "step_no": 2,
      "phase": "REMEDIATION",
      "system_id": "backup_service",
      "resource_id": "backup_3245",
      "operation": "BLOCK_RESTORE",
      "state": "BLOCKED",
      "evidence_id": ""
    },
    {
      "step_no": 3,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_4092",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 4,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_1797",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    },
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "backup_service",
      "resource_id": "backup_3245",
      "operation": "VERIFY_RESTORE_BLOCKED",
      "state": "BLOCKED",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 5,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 35,
  "sequence_exact": false
}
```

## case_18

```json
{
  "case_id": "case_18",
  "expected_status": "INCOMPLETE",
  "actual_status": "INCOMPLETE",
  "status_correct": true,
  "full_case_exact": false,
  "failure": null,
  "missing_steps": [
    {
      "step_no": 9,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_5521",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 11,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_6645",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [
    {
      "expected_index": 10,
      "actual_index": 9,
      "fields": {
        "step_no": {
          "expected": 10,
          "actual": 9
        }
      }
    },
    {
      "expected_index": 12,
      "actual_index": 10,
      "fields": {
        "step_no": {
          "expected": 12,
          "actual": 10
        }
      }
    },
    {
      "expected_index": 13,
      "actual_index": 11,
      "fields": {
        "step_no": {
          "expected": 13,
          "actual": 11
        }
      }
    },
    {
      "expected_index": 14,
      "actual_index": 12,
      "fields": {
        "step_no": {
          "expected": 14,
          "actual": 12
        }
      }
    }
  ],
  "order_error": false,
  "expected_steps": 14,
  "actual_steps": 12,
  "exact_steps": 8,
  "correct_fields": 80,
  "expected_fields": 98,
  "sequence_exact": false
}
```

## case_19

```json
{
  "case_id": "case_19",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_19",
    "failure_type": "investigation_unresolved",
    "reason": "request_intent",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "FINDING",
      "system_id": "search_service",
      "resource_id": "search_6083",
      "operation": "REPORT_REMAINING_RECORD",
      "state": "PRESENT",
      "evidence_id": "evidence_01"
    },
    {
      "step_no": 2,
      "phase": "FINDING",
      "system_id": "support_platform",
      "resource_id": "support_9553",
      "operation": "REPORT_EXPOSED_PII",
      "state": "PRESENT",
      "evidence_id": "evidence_01"
    },
    {
      "step_no": 3,
      "phase": "REMEDIATION",
      "system_id": "search_service",
      "resource_id": "search_6083",
      "operation": "DELETE_RECORD",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 4,
      "phase": "REMEDIATION",
      "system_id": "support_platform",
      "resource_id": "support_9553",
      "operation": "REDACT_RECORD",
      "state": "REDACTED",
      "evidence_id": ""
    },
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_9102",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 6,
      "phase": "VERIFICATION",
      "system_id": "search_service",
      "resource_id": "search_6083",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 7,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_6793",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    },
    {
      "step_no": 8,
      "phase": "VERIFICATION",
      "system_id": "support_platform",
      "resource_id": "support_9553",
      "operation": "VERIFY_RECORD_REDACTED",
      "state": "REDACTED",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 8,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 56,
  "sequence_exact": false
}
```

## case_20

```json
{
  "case_id": "case_20",
  "expected_status": "INCOMPLETE",
  "actual_status": "INCOMPLETE",
  "status_correct": true,
  "full_case_exact": false,
  "failure": null,
  "missing_steps": [
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_5037",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 7,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_5569",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [
    {
      "expected_index": 6,
      "actual_index": 5,
      "fields": {
        "step_no": {
          "expected": 6,
          "actual": 5
        }
      }
    },
    {
      "expected_index": 8,
      "actual_index": 6,
      "fields": {
        "step_no": {
          "expected": 8,
          "actual": 6
        }
      }
    }
  ],
  "order_error": false,
  "expected_steps": 8,
  "actual_steps": 6,
  "exact_steps": 4,
  "correct_fields": 40,
  "expected_fields": 56,
  "sequence_exact": false
}
```

## case_21

```json
{
  "case_id": "case_21",
  "expected_status": "COMPLETE",
  "actual_status": "COMPLETE",
  "status_correct": true,
  "full_case_exact": false,
  "failure": null,
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_6440",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 3,
      "phase": "VERIFICATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_5335",
      "operation": "VERIFY_RECORD_ANONYMIZED",
      "state": "ANONYMIZED",
      "evidence_id": "evidence_92"
    }
  ],
  "extra_steps": [],
  "field_errors": [
    {
      "expected_index": 2,
      "actual_index": 1,
      "fields": {
        "step_no": {
          "expected": 2,
          "actual": 1
        }
      }
    }
  ],
  "order_error": false,
  "expected_steps": 3,
  "actual_steps": 1,
  "exact_steps": 0,
  "correct_fields": 6,
  "expected_fields": 21,
  "sequence_exact": false
}
```

## case_22

```json
{
  "case_id": "case_22",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_22",
    "failure_type": "policy_unresolved",
    "reason": null,
    "stage": "compile_plan"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "FINDING",
      "system_id": "search_service",
      "resource_id": "search_8911",
      "operation": "REPORT_REMAINING_RECORD",
      "state": "PRESENT",
      "evidence_id": "evidence_05"
    },
    {
      "step_no": 2,
      "phase": "FINDING",
      "system_id": "analytics_platform",
      "resource_id": "analytics_4440",
      "operation": "REPORT_EXPOSED_PII",
      "state": "PRESENT",
      "evidence_id": "evidence_05"
    },
    {
      "step_no": 3,
      "phase": "REMEDIATION",
      "system_id": "search_service",
      "resource_id": "search_8911",
      "operation": "DELETE_RECORD",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 4,
      "phase": "REMEDIATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_4440",
      "operation": "ANONYMIZE_RECORD",
      "state": "ANONYMIZED",
      "evidence_id": ""
    },
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_4990",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 6,
      "phase": "VERIFICATION",
      "system_id": "search_service",
      "resource_id": "search_8911",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 7,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_3482",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    },
    {
      "step_no": 8,
      "phase": "VERIFICATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_4440",
      "operation": "VERIFY_RECORD_ANONYMIZED",
      "state": "ANONYMIZED",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 8,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 56,
  "sequence_exact": false
}
```

## case_23

```json
{
  "case_id": "case_23",
  "expected_status": "INCOMPLETE",
  "actual_status": "INCOMPLETE",
  "status_correct": true,
  "full_case_exact": false,
  "failure": null,
  "missing_steps": [
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_410",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 8,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_4128",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [
    {
      "expected_index": 6,
      "actual_index": 5,
      "fields": {
        "step_no": {
          "expected": 6,
          "actual": 5
        }
      }
    },
    {
      "expected_index": 7,
      "actual_index": 6,
      "fields": {
        "step_no": {
          "expected": 7,
          "actual": 6
        }
      }
    }
  ],
  "order_error": false,
  "expected_steps": 8,
  "actual_steps": 6,
  "exact_steps": 4,
  "correct_fields": 40,
  "expected_fields": 56,
  "sequence_exact": false
}
```

## case_24

```json
{
  "case_id": "case_24",
  "expected_status": "INCOMPLETE",
  "actual_status": "INCOMPLETE",
  "status_correct": true,
  "full_case_exact": false,
  "failure": null,
  "missing_steps": [
    {
      "step_no": 7,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_7095",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 7,
  "actual_steps": 6,
  "exact_steps": 6,
  "correct_fields": 42,
  "expected_fields": 49,
  "sequence_exact": false
}
```

## case_25

```json
{
  "case_id": "case_25",
  "expected_status": "COMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_25",
    "failure_type": "investigation_unresolved",
    "reason": "request_intent",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_3136",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 2,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_451",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 3,
      "phase": "VERIFICATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_1895",
      "operation": "VERIFY_RECORD_ANONYMIZED",
      "state": "ANONYMIZED",
      "evidence_id": "evidence_92"
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 3,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 21,
  "sequence_exact": false
}
```

## case_26

```json
{
  "case_id": "case_26",
  "expected_status": "COMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_26",
    "failure_type": "investigation_unresolved",
    "reason": "request_intent",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_5684",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 2,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_5416",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 3,
      "phase": "VERIFICATION",
      "system_id": "support_platform",
      "resource_id": "support_4715",
      "operation": "VERIFY_RECORD_REDACTED",
      "state": "REDACTED",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 4,
      "phase": "VERIFICATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_4566",
      "operation": "VERIFY_RECORD_ANONYMIZED",
      "state": "ANONYMIZED",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "integration_service",
      "resource_id": "data_flow_6244",
      "operation": "VERIFY_DATA_FLOW_DISABLED",
      "state": "DISABLED",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 6,
      "phase": "VERIFICATION",
      "system_id": "backup_service",
      "resource_id": "backup_3120",
      "operation": "VERIFY_RESTORE_BLOCKED",
      "state": "BLOCKED",
      "evidence_id": "evidence_92"
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 6,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 42,
  "sequence_exact": false
}
```

## case_27

```json
{
  "case_id": "case_27",
  "expected_status": "COMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_27",
    "failure_type": "investigation_unresolved",
    "reason": "request_intent",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_3866",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 2,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_3830",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 3,
      "phase": "VERIFICATION",
      "system_id": "support_platform",
      "resource_id": "support_4707",
      "operation": "VERIFY_RECORD_REDACTED",
      "state": "REDACTED",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 4,
      "phase": "VERIFICATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_4574",
      "operation": "VERIFY_RECORD_ANONYMIZED",
      "state": "ANONYMIZED",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "integration_service",
      "resource_id": "data_flow_2295",
      "operation": "VERIFY_DATA_FLOW_DISABLED",
      "state": "DISABLED",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 6,
      "phase": "VERIFICATION",
      "system_id": "backup_service",
      "resource_id": "backup_5970",
      "operation": "VERIFY_RESTORE_BLOCKED",
      "state": "BLOCKED",
      "evidence_id": "evidence_92"
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 6,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 42,
  "sequence_exact": false
}
```

## case_28

```json
{
  "case_id": "case_28",
  "expected_status": "COMPLETE",
  "actual_status": "COMPLETE",
  "status_correct": true,
  "full_case_exact": false,
  "failure": null,
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_5482",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 4,
      "phase": "VERIFICATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_6077",
      "operation": "VERIFY_RECORD_ANONYMIZED",
      "state": "ANONYMIZED",
      "evidence_id": "evidence_92"
    }
  ],
  "extra_steps": [],
  "field_errors": [
    {
      "expected_index": 2,
      "actual_index": 1,
      "fields": {
        "step_no": {
          "expected": 2,
          "actual": 1
        }
      }
    },
    {
      "expected_index": 3,
      "actual_index": 2,
      "fields": {
        "step_no": {
          "expected": 3,
          "actual": 2
        }
      }
    },
    {
      "expected_index": 5,
      "actual_index": 3,
      "fields": {
        "step_no": {
          "expected": 5,
          "actual": 3
        }
      }
    },
    {
      "expected_index": 6,
      "actual_index": 4,
      "fields": {
        "step_no": {
          "expected": 6,
          "actual": 4
        }
      }
    }
  ],
  "order_error": false,
  "expected_steps": 6,
  "actual_steps": 4,
  "exact_steps": 0,
  "correct_fields": 24,
  "expected_fields": 42,
  "sequence_exact": false
}
```

## case_29

```json
{
  "case_id": "case_29",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_29",
    "failure_type": "investigation_unresolved",
    "reason": "request_intent",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "FINDING",
      "system_id": "search_service",
      "resource_id": "search_1993",
      "operation": "REPORT_REMAINING_RECORD",
      "state": "PRESENT",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 2,
      "phase": "FINDING",
      "system_id": "analytics_platform",
      "resource_id": "analytics_5208",
      "operation": "REPORT_EXPOSED_PII",
      "state": "PRESENT",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 3,
      "phase": "FINDING",
      "system_id": "support_platform",
      "resource_id": "support_5281",
      "operation": "REPORT_EXPOSED_PII",
      "state": "PRESENT",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 4,
      "phase": "FINDING",
      "system_id": "integration_service",
      "resource_id": "data_flow_3827",
      "operation": "REPORT_ACTIVE_DATA_FLOW",
      "state": "ACTIVE",
      "evidence_id": "evidence_92"
    },
    {
      "step_no": 5,
      "phase": "REMEDIATION",
      "system_id": "integration_service",
      "resource_id": "data_flow_3827",
      "operation": "DISABLE_DATA_FLOW",
      "state": "DISABLED",
      "evidence_id": ""
    },
    {
      "step_no": 6,
      "phase": "REMEDIATION",
      "system_id": "search_service",
      "resource_id": "search_1993",
      "operation": "DELETE_RECORD",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 7,
      "phase": "REMEDIATION",
      "system_id": "support_platform",
      "resource_id": "support_5281",
      "operation": "REDACT_RECORD",
      "state": "REDACTED",
      "evidence_id": ""
    },
    {
      "step_no": 8,
      "phase": "REMEDIATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_5208",
      "operation": "ANONYMIZE_RECORD",
      "state": "ANONYMIZED",
      "evidence_id": ""
    },
    {
      "step_no": 9,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_7012",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 10,
      "phase": "VERIFICATION",
      "system_id": "search_service",
      "resource_id": "search_1993",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 11,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_3954",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    },
    {
      "step_no": 12,
      "phase": "VERIFICATION",
      "system_id": "support_platform",
      "resource_id": "support_5281",
      "operation": "VERIFY_RECORD_REDACTED",
      "state": "REDACTED",
      "evidence_id": ""
    },
    {
      "step_no": 13,
      "phase": "VERIFICATION",
      "system_id": "analytics_platform",
      "resource_id": "analytics_5208",
      "operation": "VERIFY_RECORD_ANONYMIZED",
      "state": "ANONYMIZED",
      "evidence_id": ""
    },
    {
      "step_no": 14,
      "phase": "VERIFICATION",
      "system_id": "integration_service",
      "resource_id": "data_flow_3827",
      "operation": "VERIFY_DATA_FLOW_DISABLED",
      "state": "DISABLED",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 14,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 98,
  "sequence_exact": false
}
```

## case_30

```json
{
  "case_id": "case_30",
  "expected_status": "INCOMPLETE",
  "actual_status": "INCOMPLETE",
  "status_correct": true,
  "full_case_exact": false,
  "failure": null,
  "missing_steps": [
    {
      "step_no": 9,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_4163",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 11,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_1707",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [
    {
      "expected_index": 10,
      "actual_index": 9,
      "fields": {
        "step_no": {
          "expected": 10,
          "actual": 9
        }
      }
    },
    {
      "expected_index": 12,
      "actual_index": 10,
      "fields": {
        "step_no": {
          "expected": 12,
          "actual": 10
        }
      }
    },
    {
      "expected_index": 13,
      "actual_index": 11,
      "fields": {
        "step_no": {
          "expected": 13,
          "actual": 11
        }
      }
    },
    {
      "expected_index": 14,
      "actual_index": 12,
      "fields": {
        "step_no": {
          "expected": 14,
          "actual": 12
        }
      }
    }
  ],
  "order_error": false,
  "expected_steps": 14,
  "actual_steps": 12,
  "exact_steps": 8,
  "correct_fields": 80,
  "expected_fields": 98,
  "sequence_exact": false
}
```

## case_31

```json
{
  "case_id": "case_31",
  "expected_status": "COMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_31",
    "failure_type": "investigation_unresolved",
    "reason": "request_intent",
    "stage": "investigate"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_4857",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": "evidence_51"
    },
    {
      "step_no": 2,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_6909",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": "evidence_51"
    },
    {
      "step_no": 3,
      "phase": "VERIFICATION",
      "system_id": "identity_service",
      "resource_id": "tombstone_440",
      "operation": "VERIFY_RECORD_REDACTED",
      "state": "REDACTED",
      "evidence_id": "evidence_51"
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 3,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 21,
  "sequence_exact": false
}
```

## case_32

```json
{
  "case_id": "case_32",
  "expected_status": "INCOMPLETE",
  "actual_status": null,
  "status_correct": false,
  "full_case_exact": false,
  "failure": {
    "case_id": "case_32",
    "failure_type": "policy_unresolved",
    "reason": null,
    "stage": "compile_plan"
  },
  "missing_steps": [
    {
      "step_no": 1,
      "phase": "FINDING",
      "system_id": "identity_service",
      "resource_id": "tombstone_9178",
      "operation": "REPORT_EXPOSED_PII",
      "state": "PRESENT",
      "evidence_id": "evidence_51"
    },
    {
      "step_no": 2,
      "phase": "REMEDIATION",
      "system_id": "identity_service",
      "resource_id": "tombstone_9178",
      "operation": "REDACT_RECORD",
      "state": "REDACTED",
      "evidence_id": ""
    },
    {
      "step_no": 3,
      "phase": "VERIFICATION",
      "system_id": "account_service",
      "resource_id": "account_8858",
      "operation": "VERIFY_RECORD_ABSENT",
      "state": "ABSENT",
      "evidence_id": ""
    },
    {
      "step_no": 4,
      "phase": "VERIFICATION",
      "system_id": "security_service",
      "resource_id": "audit_record_7068",
      "operation": "VERIFY_RECORD_PRESENT",
      "state": "PRESENT",
      "evidence_id": ""
    },
    {
      "step_no": 5,
      "phase": "VERIFICATION",
      "system_id": "identity_service",
      "resource_id": "tombstone_9178",
      "operation": "VERIFY_RECORD_REDACTED",
      "state": "REDACTED",
      "evidence_id": ""
    }
  ],
  "extra_steps": [],
  "field_errors": [],
  "order_error": false,
  "expected_steps": 5,
  "actual_steps": 0,
  "exact_steps": 0,
  "correct_fields": 0,
  "expected_fields": 35,
  "sequence_exact": false
}
```
