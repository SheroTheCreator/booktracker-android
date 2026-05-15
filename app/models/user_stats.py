from peewee import *
from app.models.book import db, BaseModel


class UserStats(BaseModel):
    yearly_goal  = IntegerField(default=12)
    monthly_goal = IntegerField(default=1)
    daily_pages  = IntegerField(default=10)

    class Meta:
        table_name = 'user_stats'


def get_or_create_stats():
    db.connect(reuse_if_open=True)
    db.create_tables([UserStats], safe=True)
    stats, _ = UserStats.get_or_create(
        id=1,
        defaults={'yearly_goal': 12, 'monthly_goal': 1, 'daily_pages': 10},
    )
    return stats
