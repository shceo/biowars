# models/statistics.py
from tortoise import fields, models

class Statistics(models.Model):
    id                = fields.IntField(pk=True)
    # связь «один к одному» с лабораторией
    lab: fields.OneToOneRelation["Laboratory"] = fields.OneToOneField(
        "models.Laboratory",
        related_name="stats"
    )

    bio_experience     = fields.FloatField(default=0.0)
    bio_resource       = fields.FloatField(default=0.0)
    operations_total   = fields.IntField(default=0)
    operations_done    = fields.IntField(default=0)
    operations_blocked = fields.IntField(default=0)
    infected_count     = fields.IntField(default=0)
    own_diseases       = fields.IntField(default=0)

    class Meta:
        table = "lab_statistics"
