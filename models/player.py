# models/player.py
from tortoise import fields, models

class Player(models.Model):
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True)
    username     = fields.CharField(max_length=32, null=True)
    full_name    = fields.CharField(max_length=255, null=True)
    created_at   = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "players"
