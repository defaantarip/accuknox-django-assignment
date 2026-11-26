# Django Trainee Assignment

Django signal experiments and a custom iterable `Rectangle` class.

## Setup

Use **Python 3.8 to 3.10**. The project uses **Django 3.2.25** to match the
documentation linked in the assignment. Django 3.2 no longer receives support,
so this version is for the assignment, not for a new production project.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py prove_signals  # prints the observed evidence
python manage.py test           # asserts it
```

The snippets below are shortened. The linked files contain the complete code.

## Q1. Are signals synchronous or asynchronous by default?

**Synchronous.** `send()` calls each synchronous receiver and returns only after
they have finished (or one raises an exception).

```python
def slow_receiver(**kwargs):
    events.append("receiver started")
    time.sleep(1)
    events.append("receiver finished")

events.append("before send")
demo_signal.send(sender=sender)
events.append("after send")
# before send -> receiver started -> receiver finished -> after send
```

**Why this shows it:** if the caller did not wait, `after send` could be recorded
during the one-second sleep. Instead it comes after `receiver finished`, and
`send()` takes about one second.

Code: [`q1_synchronous.py`](signals_demo/proofs/q1_synchronous.py)

## Q2. Do signals run in the same thread as the caller?

**Yes, for synchronous receivers called with `send()`.**

```python
local = threading.local()
local.value = "set by caller"

def receiver(**kwargs):
    seen["receiver_thread_id"] = threading.get_ident()
    seen["receiver_sees_thread_local"] = getattr(local, "value", None)

seen["caller_thread_id"] = threading.get_ident()
demo_signal.send(sender=sender)
```

**Why this shows it:** the thread IDs match, and the receiver can read a
thread-local value that only the caller's thread can see. This also holds when
the caller is a worker thread, so the receiver follows the caller rather than
always using the main thread.

A receiver can still start its own thread or queue a task. That later work is
outside this claim. Newer Django versions also support async receivers, which
are not covered here.

Code: [`q2_same_thread.py`](signals_demo/proofs/q2_same_thread.py)

## Q3. Do signals run in the same database transaction as the caller?

**Yes. A synchronous receiver using the same database runs on the caller's
connection, inside any transaction open on it.** This example uses the built-in
`post_save` signal.

```python
def receiver(sender, instance, **kwargs):
    ReceiverRecord.objects.create(marker=instance.marker)

post_save.connect(receiver, sender=CallerRecord)

try:
    with transaction.atomic():
        CallerRecord.objects.create(marker="x")  # receiver writes here
        raise ForcedRollback()                  # caller fails afterwards
except ForcedRollback:
    pass

assert not CallerRecord.objects.filter(marker="x").exists()
assert not ReceiverRecord.objects.filter(marker="x").exists()
```

**Why this shows it:** both rows exist before the rollback and neither exists
after it. The receiver's write was undone by the caller's transaction. If the
receiver had committed independently, its row would remain.

The full code runs three experiments:

| Experiment | Caller row afterwards | Receiver row afterwards |
|---|---|---|
| Caller raises inside `atomic()` | removed | removed |
| Receiver raises inside `atomic()`, exception leaves the block | removed | removed |
| Receiver raises **without** `atomic()` | **saved** | **saved** |

The third result matters: **a signal does not create a shared transaction.**
Django uses autocommit by default. In this simple, single-table model, each
write is committed as it happens, so a later receiver error does not undo either
one.

This does not cover writes to a different database, work moved to another thread
or task queue, or callbacks deferred with `transaction.on_commit()`.

Code: [`q3_transaction.py`](signals_demo/proofs/q3_transaction.py)

The tests use `TransactionTestCase` because `TestCase` wraps each test in its own
transaction, which would hide the autocommit behaviour.

## Custom class: Rectangle

```python
class Rectangle:
    def __init__(self, length: int, width: int):
        self.length = length
        self.width = width

    def __iter__(self):
        yield {"length": self.length}
        yield {"width": self.width}
```

```bash
python manage.py shell -c "from shapes.rectangle import Rectangle; print(*Rectangle(10, 5), sep='\n')"
```

```text
{'length': 10}
{'width': 5}
```

`__iter__` is a generator, so each loop gets a fresh iterator and the same object
can be iterated more than once. The `int` annotations are type hints; Python does
not enforce them at runtime. The assignment's `{width: ...}` is read as
`{'width': ...}`.

Code: [`rectangle.py`](shapes/rectangle.py)

## Reference

[Django 3.2 signals documentation](https://docs.djangoproject.com/en/3.2/topics/signals/)
