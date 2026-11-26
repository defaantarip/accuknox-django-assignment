"""Q2: With send() and a synchronous receiver, it runs in the caller's thread."""
import threading

from signals_demo.signals import demo_signal, temporary_receiver


def _send_and_observe():
    sender = object()
    local = threading.local()  # values here are visible to one thread only
    local.value = "set by caller"
    seen = {}

    def receiver(**kwargs):
        seen["receiver_thread_id"] = threading.get_ident()
        seen["receiver_sees_thread_local"] = getattr(local, "value", None)

    with temporary_receiver(demo_signal, receiver, sender):
        seen["caller_thread_id"] = threading.get_ident()
        demo_signal.send(sender=sender)

    return seen


def run():
    from_current_thread = _send_and_observe()

    # Repeat from another thread: the receiver should follow the caller,
    # not simply always run on the main thread.
    result = {}
    worker = threading.Thread(target=lambda: result.update(_send_and_observe()))
    worker.start()
    worker.join()

    return {"current_thread": from_current_thread, "worker_thread": result}
