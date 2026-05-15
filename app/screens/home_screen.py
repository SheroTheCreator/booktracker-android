from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.widget import Widget


class BookCard(MDCard):
    def __init__(self, book, on_select, **kwargs):
        super().__init__(**kwargs)
        self.book = book
        self.on_select = on_select
        self.size_hint = (None, None)
        self.size = (dp(140), dp(220))
        self.padding = dp(8)
        self.spacing = dp(4)
        self.elevation = 2
        self.radius = [dp(12)]
        self.orientation = 'vertical'

        cover = MDLabel(
            text='[Cover]',
            halign='center',
            size_hint_y=0.65,
            theme_text_color='Secondary',
        )
        title = MDLabel(
            text=book.title,
            halign='center',
            font_style='Caption',
            size_hint_y=0.2,
        )
        author = MDLabel(
            text=book.author,
            halign='center',
            font_style='Overline',
            size_hint_y=0.15,
            theme_text_color='Secondary',
        )
        self.add_widget(cover)
        self.add_widget(title)
        self.add_widget(author)
        self.bind(on_release=lambda *a: on_select(book.id))


class UpdateProgressDialog:
    def __init__(self, current_page, total_pages, on_confirm):
        self.on_confirm = on_confirm
        self.current_page = current_page
        self.total_pages = total_pages

        self.end_page_field = MDTextField(
            hint_text=f'End Page (current: {current_page})',
            input_filter='int',
        )
        self.minutes_field = MDTextField(
            hint_text='Minutes Spent',
            input_filter='int',
        )
        self.error_label = MDLabel(text='', theme_text_color='Error', size_hint_y=None, height=dp(20))

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(12),
            size_hint_y=None,
            height=dp(160),
        )
        content.add_widget(self.end_page_field)
        content.add_widget(self.minutes_field)
        content.add_widget(self.error_label)

        self.dialog = MDDialog(
            title='Update Progress',
            type='custom',
            content_cls=content,
            buttons=[
                MDRaisedButton(text='Cancel', on_release=lambda *a: self.dialog.dismiss()),
                MDRaisedButton(text='Save', on_release=self._validate),
            ],
        )

    def _validate(self, *args):
        try:
            ep = int(self.end_page_field.text or 0)
            mins = int(self.minutes_field.text or 0)
        except ValueError:
            self.error_label.text = 'Please enter valid numbers.'
            return
        if ep <= self.current_page:
            self.error_label.text = 'End page must be > current page.'
            return
        if ep > self.total_pages:
            self.error_label.text = f'End page must be <= {self.total_pages}.'
            return
        if mins < 1:
            self.error_label.text = 'Minutes must be >= 1.'
            return
        self.dialog.dismiss()
        self.on_confirm(ep, mins)

    def open(self):
        self.dialog.open()


class AddQuoteDialog:
    def __init__(self, on_confirm):
        self.on_confirm = on_confirm
        self.text_field = MDTextField(
            hint_text='Enter quote...',
            multiline=True,
            max_height=dp(100),
        )
        content = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
        )
        content.add_widget(self.text_field)
        self.dialog = MDDialog(
            title='Add Quote',
            type='custom',
            content_cls=content,
            buttons=[
                MDRaisedButton(text='Cancel', on_release=lambda *a: self.dialog.dismiss()),
                MDRaisedButton(text='Save', on_release=self._save),
            ],
        )

    def _save(self, *args):
        text = self.text_field.text.strip()
        if text:
            self.dialog.dismiss()
            self.on_confirm(text)

    def open(self):
        self.dialog.open()


class HomeScreen(MDScreen):
    def __init__(self, viewmodel, **kwargs):
        super().__init__(name='home', **kwargs)
        self.vm = viewmodel
        self.vm.observe(self._on_state_changed)
        self._build_ui()
        self._on_state_changed()

    # ------------------------------------------------------------------ build

    def _build_ui(self):
        root = ScrollView()
        self.layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            padding=[dp(16), dp(16), dp(16), dp(32)],
            size_hint_y=None,
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))

        # --- Header: yearly goal ---
        self.goal_label = MDLabel(
            text='Year Goal',
            font_style='H6',
            size_hint_y=None,
            height=dp(30),
        )
        self.goal_progress_label = MDLabel(
            text='0 / 0',
            size_hint_y=None,
            height=dp(22),
            theme_text_color='Secondary',
        )
        self.goal_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(8))

        # --- Carousel placeholder (horizontal scroll) ---
        self.carousel_scroll = ScrollView(
            do_scroll_x=True,
            do_scroll_y=False,
            size_hint_y=None,
            height=dp(240),
        )
        self.carousel_box = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(12),
            size_hint_x=None,
            padding=[dp(8), 0],
        )
        self.carousel_box.bind(minimum_width=self.carousel_box.setter('width'))
        self.carousel_scroll.add_widget(self.carousel_box)

        # --- Empty state ---
        self.empty_box = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(240),
            spacing=dp(12),
        )
        self.empty_label = MDLabel(
            text='No books in progress',
            halign='center',
            font_style='H6',
            theme_text_color='Secondary',
        )
        self.go_library_btn = MDRaisedButton(
            text='Go to Library',
            pos_hint={'center_x': 0.5},
            on_release=self._go_library,
        )
        self.empty_box.add_widget(Widget())
        self.empty_box.add_widget(self.empty_label)
        self.empty_box.add_widget(self.go_library_btn)
        self.empty_box.add_widget(Widget())

        # --- Progress block ---
        self.progress_label = MDLabel(
            text='0 / 0 pages',
            size_hint_y=None,
            height=dp(22),
            theme_text_color='Secondary',
        )
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))

        # --- Action buttons ---
        btn_row = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(12),
            size_hint_y=None,
            height=dp(48),
        )
        self.start_btn = MDRaisedButton(
            text='Start Reading',
            on_release=self._start_reading,
        )
        self.update_btn = MDRaisedButton(
            text='Update Progress',
            on_release=self._update_progress,
        )
        btn_row.add_widget(self.start_btn)
        btn_row.add_widget(self.update_btn)

        # --- Quote button ---
        quote_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(48),
        )
        quote_row.add_widget(Widget())
        self.quote_btn = MDIconButton(
            icon='pencil',
            on_release=self._add_quote,
        )
        quote_row.add_widget(self.quote_btn)

        for w in [
            self.goal_label, self.goal_progress_label, self.goal_bar,
            self.carousel_scroll,
            self.empty_box,
            self.progress_label, self.progress_bar,
            btn_row, quote_row,
        ]:
            self.layout.add_widget(w)

        root.add_widget(self.layout)
        self.add_widget(root)

    # ------------------------------------------------------------------ state

    def _on_state_changed(self):
        books = self.vm.books
        goal = self.vm.yearly_goal
        finished = self.vm.finished_count

        # Header
        self.goal_label.text = 'Year Goal'
        self.goal_progress_label.text = f'{finished} / {goal}'
        self.goal_bar.value = (finished / goal * 100) if goal else 0

        # Carousel vs empty
        if books:
            self.carousel_scroll.opacity = 1
            self.empty_box.opacity = 0
            self._rebuild_carousel(books)
            self._update_progress_block()
            self.start_btn.disabled = False
            self.update_btn.disabled = False
            self.quote_btn.disabled = False
        else:
            self.carousel_scroll.opacity = 0
            self.empty_box.opacity = 1
            self.progress_label.text = '0 / 0 pages'
            self.progress_bar.value = 0
            self.start_btn.disabled = True
            self.update_btn.disabled = True
            self.quote_btn.disabled = True

    def _rebuild_carousel(self, books):
        self.carousel_box.clear_widgets()
        selected = self.vm.selected_book
        for book in books:
            card = BookCard(
                book=book,
                on_select=self._on_book_selected,
            )
            if selected and book.id == selected.id:
                card.scale = 1.0
                card.elevation = 6
            else:
                card.scale = 0.9
                card.elevation = 2
            self.carousel_box.add_widget(card)

    def _update_progress_block(self):
        book = self.vm.selected_book
        if book is None:
            return
        total = book.total_pages or 1
        pct = book.current_page / total
        anim = Animation(value=pct * 100, duration=0.4)
        anim.start(self.progress_bar)
        self.progress_label.text = f'{book.current_page} / {book.total_pages} pages'

    # ------------------------------------------------------------------ actions

    def _on_book_selected(self, book_id):
        self.vm.select_book(book_id)

    def _start_reading(self, *args):
        book = self.vm.selected_book
        if book:
            app = self.manager.get_screen('timer')
            app.set_book(book, self.vm)
            self.manager.current = 'timer'

    def _update_progress(self, *args):
        book = self.vm.selected_book
        if book:
            dlg = UpdateProgressDialog(
                current_page=book.current_page,
                total_pages=book.total_pages,
                on_confirm=self.vm.update_progress,
            )
            dlg.open()

    def _add_quote(self, *args):
        dlg = AddQuoteDialog(on_confirm=self.vm.add_quote)
        dlg.open()

    def _go_library(self, *args):
        if self.manager.has_screen('library'):
            self.manager.current = 'library'
