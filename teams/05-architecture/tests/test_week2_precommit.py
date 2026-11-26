"""G5 delegates D3 ownership transitions to the public G7 interface."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from pathlib import Path
import sys

TEAM = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(TEAM / 'harness'), str(TEAM.parent / '07-infrastructure')]
from ckpt.ckpt import CheckpointError, FencedError
from week2.precommit import claim_initial_state


class PrecommitTests(unittest.TestCase):
    def test_delegates_fresh_and_explicit_recovery_without_private_writes(self):
        for recovering, epoch in ((False, 1), (True, 3)):
            with self.subTest(recovering=recovering):
                api = Mock(return_value=epoch)
                attempt = SimpleNamespace(claim_initial=api)
                result = claim_initial_state(attempt, identity_sha256='a' * 64, recovering=recovering)
                api.assert_called_once_with('a' * 64, allow_takeover=recovering)
                self.assertEqual(result, {'previous_epoch': epoch - 1, 'epoch': epoch})
                self.assertEqual(set(vars(attempt)), {'claim_initial'})

    def test_missing_public_interface_holds(self):
        with self.assertRaises(CheckpointError):
            claim_initial_state(SimpleNamespace(), identity_sha256='a' * 64, recovering=True)

    def test_preserves_public_api_fencing_error(self):
        error = FencedError('another attempt committed')
        with self.assertRaises(FencedError) as caught:
            claim_initial_state(SimpleNamespace(claim_initial=Mock(side_effect=error)),
                                identity_sha256='a' * 64, recovering=True)
        self.assertIs(caught.exception, error)


if __name__ == '__main__':
    unittest.main()
