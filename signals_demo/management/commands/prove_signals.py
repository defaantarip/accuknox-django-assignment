import json

from django.core.management.base import BaseCommand

from signals_demo.proofs import q1_synchronous, q2_same_thread, q3_transaction


class Command(BaseCommand):
    help = "Run the signal experiments and print what was observed."

    def handle(self, *args, **options):
        proofs = (
            ("Q1: synchronous execution", q1_synchronous),
            ("Q2: caller's thread", q2_same_thread),
            ("Q3: caller's transaction", q3_transaction),
        )
        for title, proof in proofs:
            self.stdout.write(self.style.MIGRATE_HEADING(title))
            self.stdout.write(json.dumps(proof.run(), indent=2))
