# models/skill.py
from tortoise import fields, models

class Skill(models.Model):
    id            = fields.IntField(pk=True)
    # связь «много к одному» с лабораторией
    lab: fields.ForeignKeyRelation["Laboratory"] = fields.ForeignKeyField(
        "models.Laboratory",
        related_name="skills"
    )

    infectivity   = fields.IntField(default=0)
    immunity      = fields.IntField(default=0)
    lethality     = fields.IntField(default=0)
    safety        = fields.IntField(default=0)
    qualification = fields.IntField(default=0)

    class Meta:
        table = "lab_skills"
