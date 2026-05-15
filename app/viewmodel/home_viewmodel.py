from app.repository.repository import BookRepository


class HomeViewModel:
    """
    Reactive-style ViewModel for Home Screen.
    Observers are simple callables stored in lists.
    """

    def __init__(self):
        self.repo = BookRepository()
        self._books = []
        self._selected_book_id = None
        self._yearly_goal = 12
        self._finished_count = 0
        self._observers = []
        self.refresh()

    # ---------- Public state ----------

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
    def yearly_goal(self):
        return self._yearly_goal

    @property
    def finished_count(self):
        return self._finished_count

    # ---------- Actions ----------

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
        self._books = self.repo.get_active_books()
        self._yearly_goal = self.repo.get_yearly_goal()
        self._finished_count = self.repo.get_finished_this_year()
        # Keep selection valid
        ids = [b.id for b in self._books]
        if self._selected_book_id not in ids:
            self._selected_book_id = ids[0] if ids else None
        self._notify()

    # ---------- Observer pattern ----------

    def observe(self, callback):
        self._observers.append(callback)

    def _notify(self):
        for cb in self._observers:
            cb()
