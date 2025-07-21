# models/laboratory.py
from tortoise import fields, models

class Laboratory(models.Model):
    id = fields.IntField(pk=True)
    player = fields.OneToOneField("models.Player", related_name="lab")
    corporation = fields.ForeignKeyField(
        "models.Corporation", null=True, related_name="labs"
    )
    # при желании добавьте модель Corporation, если она у вас есть
    corporation: fields.ForeignKeyNullableRelation["Corporation"] = fields.ForeignKeyField(
        "models.Corporation",
        null=True,
        related_name="labs"
    )

    activity      = fields.IntField(default=0)
    mining_bonus  = fields.IntField(default=0)
    premium_bonus = fields.IntField(default=0)

    free_pathogens   = fields.IntField(default=0)
    max_pathogens    = fields.IntField(default=0)
    next_pathogen_at = fields.DatetimeField(null=True)
    pathogen_name    = fields.CharField(max_length=100, null=True)
    fever_until      = fields.DatetimeField(null=True)
    infection_until  = fields.DatetimeField(null=True)

    class Meta:
        table = "laboratories"
