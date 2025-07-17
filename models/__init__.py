# models/__init__.py
from .player import Player
from .laboratory import Laboratory
from .skill import Skill
from .statistics import Statistics
from .corporation import Corporation   # если есть
from .pathogen import Pathogen

__all__ = [
    "Player",
    "Laboratory",
    "Skill",
    "Statistics",
    "Corporation",  # если используете
    "Pathogen",
]
