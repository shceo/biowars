from tortoise import fields, models

class Infection(models.Model):
    id = fields.IntField(pk=True)
    attacker_lab = fields.ForeignKeyField("models.Laboratory", related_name="infections_sent")
    target_lab = fields.ForeignKeyField("models.Laboratory", related_name="infections_received")
    expires_at = fields.DatetimeField(timezone=True)

    class Meta:
        table = "infections"
        unique_together = ("attacker_lab", "target_lab")

