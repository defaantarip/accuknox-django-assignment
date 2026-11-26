from contextlib import contextmanager

from django.dispatch import Signal

# A normal Django signal, used for Q1 and Q2 so no database work is involved.
demo_signal = Signal()


@contextmanager
def temporary_receiver(signal, receiver, sender):
    """Connect a receiver for one experiment, then always disconnect it."""
    signal.connect(receiver, sender=sender, weak=False)
    try:
        yield
    finally:
        signal.disconnect(receiver, sender=sender)
