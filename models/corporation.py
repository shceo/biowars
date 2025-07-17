# models/corporation.py
from tortoise import fields, models

class Corporation(models.Model):
    id    = fields.IntField(pk=True)
    name  = fields.CharField(max_length=255)
    tg_id = fields.IntField()  # для tg://openmessage?user_id=

    # обратная связь: в лаборатории укажем related_name="corporation"
    labs: fields.ReverseRelation["Laboratory"]

    class Meta:
        table = "corporations"
