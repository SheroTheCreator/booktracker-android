from peewee import *
import datetime

db = SqliteDatabase('booktracker.db')


class BaseModel(Model):
    class Meta:
        database = db


class Book(BaseModel):
    STATUS_READING   = 'READING'
    STATUS_REREADING = 'REREADING'
    STATUS_FINISHED  = 'FINISHED'
    STATUS_WISHLIST  = 'WISHLIST'

    title         = CharField()
    author        = CharField()
    cover_url     = CharField(null=True)
    total_pages   = IntegerField(default=1)
    current_page  = IntegerField(default=0)
    status        = CharField(default=STATUS_WISHLIST)
    date_added    = DateField(default=datetime.date.today)
    date_finished = DateField(null=True)

    class Meta:
        table_name = 'books'


class ReadingSession(BaseModel):
    book          = ForeignKeyField(Book, backref='sessions')
    pages_read    = IntegerField(default=0)
    minutes_spent = IntegerField(default=0)
    date          = DateField(default=datetime.date.today)

    class Meta:
        table_name = 'reading_sessions'


class Quote(BaseModel):
    book       = ForeignKeyField(Book, backref='quotes')
    text       = TextField()
    date_added = DateField(default=datetime.date.today)

    class Meta:
        table_name = 'quotes'


def _migrate(database):
    """Add columns that may be missing in older DB files (safe, idempotent)."""
    migrations = [
        "ALTER TABLE books ADD COLUMN date_added TEXT",
        "ALTER TABLE books ADD COLUMN cover_url TEXT",
        "ALTER TABLE books ADD COLUMN date_finished TEXT",
        "ALTER TABLE reading_sessions ADD COLUMN minutes_spent INTEGER DEFAULT 0",
    ]
    for sql in migrations:
        try:
            database.execute_sql(sql)
        except Exception:
            pass  # column already exists — ignore


def initialize_db():
    db.connect(reuse_if_open=True)
    _migrate(db)
    db.create_tables([Book, ReadingSession, Quote], safe=True)
