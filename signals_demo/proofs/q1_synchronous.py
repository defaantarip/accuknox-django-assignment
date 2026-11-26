"""Q1: By default, signal receivers are executed synchronously."""
import time

from signals_demo.signals import demo_signal, temporary_receiver

DELAY_SECONDS = 1.0


def run():
    events = []
    sender = object()

    def slow_receiver(**kwargs):
        events.append("receiver started")
        time.sleep(DELAY_SECONDS)
        events.append("receiver finished")

    with temporary_receiver(demo_signal, slow_receiver, sender):
        events.append("before send")
        started = time.monotonic()
        demo_signal.send(sender=sender)
        elapsed = time.monotonic() - started
        events.append("after send")

    # Asynchronous execution would let "after send" be recorded
    # without waiting for "receiver finished".
    return {"events": events, "seconds_inside_send": round(elapsed, 2)}
