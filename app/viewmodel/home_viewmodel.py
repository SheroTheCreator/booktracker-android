from app.repository.repository import BookRepository


class HomeViewModel:
    def __init__(self):
        self.repo = BookRepository()
        self._books            = []
        self._selected_book_id = None
        self._yearly_goal      = 12
        self._monthly_goal     = 1
        self._daily_pages      = 10
        self._finished_year    = 0
        self._finished_month   = 0
        self._reading_days     = set()
        self._observers        = []
        self.refresh()

    # ---------------------------------------------------------------- State

    @property
    def books(self):
        return self._books

    @property
    def selected_book(self):
        if not self._books:
            return None
        if self._selected_book_id:
            for b in self._books:
                if b.id == self._selected_book_id:
                    return b
        return self._books[0]

    @property
    def yearly_goal(self):    return self._yearly_goal
    @property
    def monthly_goal(self):   return self._monthly_goal
    @property
    def daily_pages(self):    return self._daily_pages
    @property
    def finished_count(self): return self._finished_year
    @property
    def finished_month(self): return self._finished_month
    @property
    def reading_days(self):   return self._reading_days

    # ---------------------------------------------------------------- Actions

    def select_book(self, book_id):
        self._selected_book_id = book_id
        self._notify()

    def update_progress(self, end_page: int, minutes: int):
        book = self.selected_book
        if book is None:
            return
        self.repo.update_book_page(book.id, end_page, minutes)
        self.refresh()

    def add_quote(self, text: str):
        book = self.selected_book
        if book and text.strip():
            self.repo.add_quote(book.id, text.strip())

    def refresh(self):
        self._books          = self.repo.get_active_books()
        stats                = self.repo.get_stats()
        self._yearly_goal    = stats.yearly_goal
        self._monthly_goal   = stats.monthly_goal
        self._daily_pages    = stats.daily_pages
        self._finished_year  = self.repo.get_finished_this_year()
        self._finished_month = self.repo.get_finished_this_month()
        self._reading_days   = self.repo.get_reading_days_this_month()
        ids = [b.id for b in self._books]
        if self._selected_book_id not in ids:
            self._selected_book_id = ids[0] if ids else None
        self._notify()

    # ---------------------------------------------------------------- Observer

    def observe(self, callback):
        self._observers.append(callback)

    def _notify(self):
        for cb in self._observers:
            cb()
