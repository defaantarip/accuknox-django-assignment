"""Q3: A post_save receiver shares the caller's database transaction."""
import uuid

from django.db import connection, transaction
from django.db.models.signals import post_save

from signals_demo.models import CallerRecord, ReceiverRecord
from signals_demo.signals import temporary_receiver


class ForcedRollback(Exception):
    pass


class ReceiverError(Exception):
    pass


def _counts(marker):
    return {
        "caller_rows": CallerRecord.objects.filter(marker=marker).count(),
        "receiver_rows": ReceiverRecord.objects.filter(marker=marker).count(),
    }


def _cleanup(marker):
    """Delete only the rows created by this run."""
    CallerRecord.objects.filter(marker=marker).delete()
    ReceiverRecord.objects.filter(marker=marker).delete()


def _experiment(*, use_atomic, receiver_raises):
    marker = uuid.uuid4().hex
    seen = {}

    def receiver(sender, instance, **kwargs):
        if instance.marker != marker:
            return
        seen["receiver_in_atomic_block"] = connection.in_atomic_block
        # The caller has not committed yet when use_atomic is True.
        seen["receiver_sees_caller_row"] = CallerRecord.objects.filter(
            pk=instance.pk
        ).exists()
        ReceiverRecord.objects.create(marker=marker)
        if receiver_raises:
            raise ReceiverError()

    def caller():
        CallerRecord.objects.create(marker=marker)  # fires post_save
        seen["rows_before_rollback"] = _counts(marker)
        if use_atomic:
            raise ForcedRollback()  # the CALLER fails after both writes

    try:
        with temporary_receiver(post_save, receiver, CallerRecord):
            try:
                if use_atomic:
                    with transaction.atomic():
                        caller()
                else:
                    caller()
            except (ForcedRollback, ReceiverError) as error:
                seen["exception"] = type(error).__name__
        seen["rows_afterwards"] = _counts(marker)
    finally:
        _cleanup(marker)

    return seen


def run():
    # An outer transaction would make the "no atomic()" experiment meaningless.
    if connection.in_atomic_block or not transaction.get_autocommit():
        raise RuntimeError("Run this proof in autocommit mode, outside atomic().")

    return {
        "caller_rolls_back": _experiment(use_atomic=True, receiver_raises=False),
        "receiver_raises_in_atomic": _experiment(
            use_atomic=True, receiver_raises=True
        ),
        "receiver_raises_without_atomic": _experiment(
            use_atomic=False, receiver_raises=True
        ),
    }
