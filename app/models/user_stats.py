from peewee import *
from app.models.book import db, BaseModel


class UserStats(BaseModel):
    yearly_goal  = IntegerField(default=12)
    monthly_goal = IntegerField(default=1)
    daily_pages  = IntegerField(default=10)

    class Meta:
        table_name = 'user_stats'


def _migrate_stats(database):
    migrations = [
        "ALTER TABLE user_stats ADD COLUMN yearly_goal INTEGER DEFAULT 12",
        "ALTER TABLE user_stats ADD COLUMN monthly_goal INTEGER DEFAULT 1",
        "ALTER TABLE user_stats ADD COLUMN daily_pages INTEGER DEFAULT 10",
    ]
    for sql in migrations:
        try:
            database.execute_sql(sql)
        except Exception:
            pass  # column already exists


def get_or_create_stats():
    db.connect(reuse_if_open=True)
    db.create_tables([UserStats], safe=True)
    _migrate_stats(db)
    stats, _ = UserStats.get_or_create(
        id=1,
        defaults={'yearly_goal': 12, 'monthly_goal': 1, 'daily_pages': 10},
    )
    return stats
