from django.db import models


class CallerRecord(models.Model):
    """Row written by the code that triggers the signal."""

    marker = models.CharField(max_length=32)


class ReceiverRecord(models.Model):
    """Row written by the signal receiver."""

    marker = models.CharField(max_length=32)
