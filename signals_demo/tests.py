from django.test import SimpleTestCase, TransactionTestCase

from signals_demo.proofs import q1_synchronous, q2_same_thread, q3_transaction


class SynchronousTests(SimpleTestCase):
    def test_caller_waits_for_receiver(self):
        result = q1_synchronous.run()
        self.assertEqual(
            result["events"],
            ["before send", "receiver started", "receiver finished", "after send"],
        )
        # Small tolerance for clock resolution on some platforms.
        self.assertGreaterEqual(
            result["seconds_inside_send"], q1_synchronous.DELAY_SECONDS - 0.05
        )


class SameThreadTests(SimpleTestCase):
    def test_receiver_runs_in_callers_thread(self):
        result = q2_same_thread.run()
        for seen in result.values():
            self.assertEqual(seen["caller_thread_id"], seen["receiver_thread_id"])
            self.assertEqual(seen["receiver_sees_thread_local"], "set by caller")
        self.assertNotEqual(
            result["current_thread"]["caller_thread_id"],
            result["worker_thread"]["caller_thread_id"],
        )


# TransactionTestCase does not wrap each test in a transaction.
class TransactionTests(TransactionTestCase):
    BOTH = {"caller_rows": 1, "receiver_rows": 1}
    NONE = {"caller_rows": 0, "receiver_rows": 0}

    def setUp(self):
        self.result = q3_transaction.run()

    def test_caller_rollback_removes_both_rows(self):
        seen = self.result["caller_rolls_back"]
        self.assertTrue(seen["receiver_in_atomic_block"])
        self.assertTrue(seen["receiver_sees_caller_row"])
        self.assertEqual(seen["rows_before_rollback"], self.BOTH)
        self.assertEqual(seen["exception"], "ForcedRollback")
        self.assertEqual(seen["rows_afterwards"], self.NONE)

    def test_receiver_error_rolls_back_atomic_block(self):
        seen = self.result["receiver_raises_in_atomic"]
        self.assertEqual(seen["exception"], "ReceiverError")
        self.assertEqual(seen["rows_afterwards"], self.NONE)

    def test_without_atomic_signal_creates_no_shared_transaction(self):
        seen = self.result["receiver_raises_without_atomic"]
        self.assertFalse(seen["receiver_in_atomic_block"])
        self.assertEqual(seen["exception"], "ReceiverError")
        # Each simple write was already committed in autocommit mode.
        self.assertEqual(seen["rows_afterwards"], self.BOTH)
