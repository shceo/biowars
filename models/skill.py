# models/skill.py
from tortoise import fields, models

class Skill(models.Model):
    id            = fields.IntField(pk=True)
    # связь «много к одному» с лабораторией
    lab: fields.ForeignKeyRelation["Laboratory"] = fields.ForeignKeyField(
        "models.Laboratory",
        related_name="skills"
    )

    infectivity   = fields.IntField(default=1)
    immunity      = fields.IntField(default=1)
    lethality     = fields.IntField(default=1)
    safety        = fields.IntField(default=1)
    qualification = fields.IntField(default=1)

    class Meta:
        table = "lab_skills"
