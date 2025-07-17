# models/pathogen.py
from tortoise import fields, models

class Pathogen(models.Model):
    id          = fields.IntField(pk=True)
    lab         = fields.ForeignKeyField("models.Laboratory", related_name="pathogens")
    name        = fields.CharField(max_length=100, null=True)
    created_at  = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "pathogens"
