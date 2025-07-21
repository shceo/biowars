# models/laboratory.py
from tortoise import fields, models

class Laboratory(models.Model):
    id = fields.IntField(pk=True)
    player = fields.OneToOneField("models.Player", related_name="lab")
    corporation = fields.ForeignKeyField(
        "models.Corporation", null=True, related_name="labs"
    )

    # Единственные поля с датами, все timezone‑aware:
    fever_until        = fields.DatetimeField(null=True, timezone=True)
    next_pathogen_at   = fields.DatetimeField(null=True, timezone=True)
    infection_until    = fields.DatetimeField(null=True, timezone=True)

    activity           = fields.IntField(default=0)
    mining_bonus       = fields.IntField(default=0)
    premium_bonus      = fields.IntField(default=0)

    free_pathogens     = fields.IntField(default=0)
    max_pathogens      = fields.IntField(default=0)
    pathogen_name      = fields.CharField(max_length=100, null=True)

    class Meta:
        table = "laboratories"
