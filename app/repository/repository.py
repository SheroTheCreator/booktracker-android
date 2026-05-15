import datetime
from app.models.book import Book, ReadingSession, Quote, initialize_db
from app.models.user_stats import get_or_create_stats


class BookRepository:

    def __init__(self):
        initialize_db()

    # ---------- Books ----------

    def get_active_books(self):
        """Return books with status READING or REREADING."""
        return list(
            Book.select().where(
                Book.status.in_([Book.STATUS_READING, Book.STATUS_REREADING])
            )
        )

    def get_finished_this_year(self):
        today = datetime.date.today()
        year_start = datetime.date(today.year, 1, 1)
        year_end = datetime.date(today.year, 12, 31)
        return Book.select().where(
            (Book.status == Book.STATUS_FINISHED) &
            (Book.date_finished.is_null(False)) &
            (Book.date_finished >= year_start) &
            (Book.date_finished <= year_end)
        ).count()

    def update_book_page(self, book_id: int, end_page: int, minutes: int):
        book = Book.get_by_id(book_id)
        if end_page <= book.current_page:
            raise ValueError('End page must be greater than current page.')
        if end_page > book.total_pages:
            raise ValueError('End page exceeds total pages.')
        if minutes < 1:
            raise ValueError('Minutes must be at least 1.')

        pages_read = end_page - book.current_page
        ReadingSession.create(
            book=book,
            pages_read=pages_read,
            minutes_spent=minutes,
        )
        book.current_page = end_page
        if end_page == book.total_pages:
            book.status = Book.STATUS_FINISHED
            book.date_finished = datetime.date.today()
        book.save()
        return book

    def add_quote(self, book_id: int, text: str):
        book = Book.get_by_id(book_id)
        return Quote.create(book=book, text=text)

    def get_wishlist_books(self):
        return list(Book.select().where(Book.status == 'WISHLIST'))

    # ---------- Stats ----------

    def get_yearly_goal(self):
        return get_or_create_stats().yearly_goal
