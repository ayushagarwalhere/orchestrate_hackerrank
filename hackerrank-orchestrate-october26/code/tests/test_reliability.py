"""Independent counterexamples from measured grammar/schema failure categories."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from test_iteration import artifact
from test_workflow import AT, fixture
import test_workflow as workflow
from audit_agent import AuditFailure
from audit_agent.investigation import request_authorizes
from audit_agent.readbacks import record
from evaluation.sample_eval import predict, compare


class RequestInterpretation(unittest.TestCase):
    def test_explicit_profile_removal_preserves_shared_conversations(self):
        self.assertTrue(request_authorizes("Please remove my profile. Conversations with other customers may remain."))

    def test_historical_alias_scope_is_explicit(self):
        self.assertTrue(request_authorizes("I changed the email on my account. Please remove records under both addresses."))
        self.assertTrue(request_authorizes("I changed the email on this account before deleting it. Please verify the old address is absent."))

    def test_audit_request_without_new_delete_imperative(self):
        self.assertTrue(request_authorizes("Please audit my deletion. Confirm that the account was fully removed."))
        self.assertTrue(request_authorizes("Please check that my account and profile have already been removed."))

    def test_ui_label_does_not_block_prior_deletion_audit(self):
        self.assertTrue(request_authorizes('I closed my account. Please delete the old “account settings” export.'))

    def test_quoted_instructions_are_not_authorization(self):
        for text in ['Please export the message "Please delete my account."',
                     'Please summarize `erase my account`.',
                     'Please repeat “remove my profile”.']:
            with self.subTest(text=text), self.assertRaises(AuditFailure): request_authorizes(text)

    def test_retention_condition_does_not_condition_deletion(self):
        self.assertTrue(request_authorizes("Please erase my account but you may retain logs if required by policy."))
        self.assertTrue(request_authorizes("Please remove my name and contact details from this account, keeping a reference if legally necessary."))
        self.assertTrue(request_authorizes("Delete my account. Do not delete my backups."))
        self.assertTrue(request_authorizes("Please remove my name and contact details from this account, keeping an internal deleted-account reference if required."))

    def test_deletion_conditions_are_still_unresolved(self):
        for text in ["Delete my account but only if I agree.", "Delete my account if I agree, keeping the records if needed."]:
            with self.subTest(text=text), self.assertRaises(AuditFailure): request_authorizes(text)

    def test_restoration_and_general_information_do_not_authorize_deletion(self):
        for text in ["I deleted my account accidentally. Please restore my account.",
                     "How can I delete my account?", "What does account deletion mean?",
                     "Please give me access to my account.", "Please change my email."]:
            with self.subTest(text=text): self.assertFalse(request_authorizes(text))

    def test_mixed_new_restore_and_delete_requests_remain_unresolved(self):
        with self.assertRaises(AuditFailure): request_authorizes("Please delete my account and restore my account.")
        with self.assertRaises(AuditFailure): request_authorizes("Please erase my account. I am not asking for deletion.")

    def test_information_request_negation_does_not_require_an_account_object(self):
        self.assertFalse(request_authorizes("Please send my information. This is an information request, not a request to erase it."))
        self.assertFalse(request_authorizes("Please send a copy of my information; don't delete or change anything."))

    def test_nonenglish_negation_remains_uncertain(self):
        with self.assertRaises(AuditFailure): request_authorizes("No quiero eliminar mi cuenta.")
        self.assertTrue(request_authorizes("Intenté eliminar mi cuenta. Comprueben los datos restantes."))

    def test_begin_deletion_process_is_an_imperative(self):
        self.assertTrue(request_authorizes("Please start my deletion process for this account."))
        with self.assertRaises(AuditFailure): request_authorizes("Please begin the deletion process for my account only if I approve.")

    def test_spanish_nominal_deletion_request(self):
        self.assertTrue(request_authorizes("Solicito la eliminación de mi cuenta."))
        with self.assertRaises(AuditFailure): request_authorizes("No solicito la eliminación de mi cuenta.")

    def test_portuguese_explicit_deletion_request_and_negation(self):
        self.assertTrue(request_authorizes("Peço a exclusão da minha conta."))
        with self.assertRaises(AuditFailure): request_authorizes("Não solicito a exclusão da conta.")

    def test_korean_explicit_request_and_negation(self):
        self.assertTrue(request_authorizes("제 계정의 삭제를 부탁합니다."))
        with self.assertRaises(AuditFailure): request_authorizes("계정을 삭제하지 않기를 요청합니다.")

    def test_nonenglish_conditions_require_intent_review(self):
        for text in ["Solicito la eliminación de mi cuenta si confirmo.",
                     "Solicito a exclusão da conta se eu confirmar.",
                     "Je demande la suppression de mon compte si je confirme."]:
            with self.subTest(text=text), self.assertRaises(AuditFailure): request_authorizes(text)

    def test_corrections_and_explicit_optout_negation(self):
        self.assertFalse(request_authorizes("Please replace my phone number and leave the account active."))
        self.assertFalse(request_authorizes("Please correct my name without removing my records."))
        self.assertFalse(request_authorizes("Please stop promotional emails; I am not asking for deletion."))


class SupportContext(unittest.TestCase):
    def get(self, body):
        from audit_agent.contracts import timestamp
        return record(artifact('.json', '{}'), 'support_platform', 'SUPPORT_MESSAGE',
                      dict(resource_id='opaque_ticket', requester_email='person@example.test', **body),
                      '/ticket', timestamp(AT)).observations[0]

    def test_delivery_context_is_retained_separately_from_identifiers(self):
        fact = self.get({'message_excerpt': 'Customer supplied an address for a delivery query.'})
        self.assertIn('shared_context', fact.conditions)
        self.assertEqual(fact.state.value, 'IDENTIFIABLE')

    def test_bare_identifier_is_not_context(self):
        self.assertNotIn('shared_context', self.get({}).conditions)

    def test_explicit_denial_blocks_textual_inference(self):
        self.assertNotIn('shared_context', self.get({'shared_context': False, 'message_text': 'order reference'}).conditions)


class TargetEvaluation(unittest.TestCase):
    setUp = workflow.WorkflowTests.setUp

    def test_target_run_uses_real_requests_and_cannot_read_public_answers(self):
        config = fixture(self.root)
        run = self.root / 'target_freeze'
        manifest = predict(config.dataset, run, requests_file='deletion_requests.csv', expected_cases=3)
        self.assertEqual(manifest['predicted_cases'], 3)
        with self.assertRaisesRegex(ValueError, 'Public references'):
            compare(config.dataset, run, self.root / 'report.md')
