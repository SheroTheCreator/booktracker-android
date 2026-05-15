import datetime
from app.models.book import Book, ReadingSession, Quote, initialize_db
from app.models.user_stats import get_or_create_stats


class BookRepository:

    def __init__(self):
        initialize_db()

    # ------------------------------------------------------------------ Books

    def get_active_books(self):
        return list(
            Book.select().where(
                Book.status.in_([Book.STATUS_READING, Book.STATUS_REREADING])
            ).order_by(Book.date_added)
        )

    def get_wishlist_books(self):
        return list(Book.select().where(Book.status == Book.STATUS_WISHLIST))

    def get_finished_this_year(self):
        today = datetime.date.today()
        y_start = datetime.date(today.year, 1, 1)
        y_end   = datetime.date(today.year, 12, 31)
        return Book.select().where(
            (Book.status == Book.STATUS_FINISHED) &
            (Book.date_finished.is_null(False)) &
            (Book.date_finished >= y_start) &
            (Book.date_finished <= y_end)
        ).count()

    def get_finished_this_month(self):
        today   = datetime.date.today()
        m_start = datetime.date(today.year, today.month, 1)
        import calendar as cal
        last_day = cal.monthrange(today.year, today.month)[1]
        m_end   = datetime.date(today.year, today.month, last_day)
        return Book.select().where(
            (Book.status == Book.STATUS_FINISHED) &
            (Book.date_finished.is_null(False)) &
            (Book.date_finished >= m_start) &
            (Book.date_finished <= m_end)
        ).count()

    def get_reading_days_this_month(self):
        """Return set of day-numbers that had at least one reading session."""
        today   = datetime.date.today()
        m_start = datetime.date(today.year, today.month, 1)
        import calendar as cal
        last_day = cal.monthrange(today.year, today.month)[1]
        m_end   = datetime.date(today.year, today.month, last_day)
        sessions = ReadingSession.select().where(
            (ReadingSession.date >= m_start) &
            (ReadingSession.date <= m_end)
        )
        return {s.date.day for s in sessions}

    def create_book(self, title: str, author: str, total_pages: int,
                    status: str = Book.STATUS_WISHLIST, cover_url: str = None):
        if not title.strip():
            raise ValueError('Назва не може бути порожньою.')
        if total_pages < 1:
            raise ValueError('Книга повинна мати хоча б 1 сторінку.')
        return Book.create(
            title=title.strip(),
            author=author.strip(),
            total_pages=total_pages,
            status=status,
            cover_url=cover_url,
        )

    def update_book_page(self, book_id: int, end_page: int, minutes: int):
        book = Book.get_by_id(book_id)
        if end_page <= book.current_page:
            raise ValueError('Кінцева сторінка має бути більша за поточну.')
        if end_page > book.total_pages:
            raise ValueError(f'Максимум {book.total_pages} сторінок.')
        if minutes < 1:
            raise ValueError('Мінімум 1 хвилина.')
        pages_read = end_page - book.current_page
        ReadingSession.create(book=book, pages_read=pages_read, minutes_spent=minutes)
        book.current_page = end_page
        if end_page == book.total_pages:
            book.status = Book.STATUS_FINISHED
            book.date_finished = datetime.date.today()
        book.save()
        return book

    def add_quote(self, book_id: int, text: str):
        book = Book.get_by_id(book_id)
        return Quote.create(book=book, text=text)

    # ------------------------------------------------------------------ Stats

    def get_stats(self):
        return get_or_create_stats()

    def get_yearly_goal(self):
        return get_or_create_stats().yearly_goal
