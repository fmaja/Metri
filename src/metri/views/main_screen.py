import customtkinter as ctk
from .calendar import CalendarView
from .day import DayView
from .settings import SettingsView
from .theory import TheoryView
from .quiz import QuizView
from .metronome import MetronomeView
import os
from PIL import Image


class MainScreen:
    def __init__(self, master):
        self.master = master
        master.title("Metri")

        self.container = ctk.CTkFrame(master)
        self.container.pack(fill="both", expand=True)

        self.menu_frame = ctk.CTkFrame(self.container)
        self.menu_frame.pack(fill="both", expand=True)

        header_frame = ctk.CTkFrame(self.menu_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(30, 0))

        # Try to load logo
        try:
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png")
            logo_img = ctk.CTkImage(light_image=Image.open(logo_path), size=(336, 126))
            logo_label = ctk.CTkLabel(header_frame, image=logo_img, text="")
            logo_label.pack()
        except:
            self.label = ctk.CTkLabel(
                header_frame,
                text="Welcome to Metri",
                font=("Arial", 32, "bold")
            )
            self.label.pack(pady=(10, 5))
            self.tagline = ctk.CTkLabel(
                header_frame,
                text="Your music practice companion",
                font=("Arial", 14),
                text_color="#AEB6BF"
            )
            self.tagline.pack(pady=(0, 20))

        content_frame = ctk.CTkFrame(self.menu_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=40, pady=20)

        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)

        left_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=20)

        right_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=20)

        left_panel.columnconfigure(0, weight=1)
        right_panel.columnconfigure(0, weight=1)

        button_width = 200

        ctk.CTkLabel(
            left_panel,
            text="Zarządzanie ćwiczeniami",
            font=("Arial", 18, "bold"),
            anchor="w"
        ).grid(row=0, column=0, sticky="ew", pady=(0, 15))

        self.day_button = ctk.CTkButton(
            left_panel,
            text="Przegląd dzienny",
            command=self.show_day,
            height=50,
            width=button_width,
            font=("Arial", 15),
            fg_color="#1ABC9C",
            hover_color="#16A085",
            corner_radius=10,
            border_spacing=10,
            anchor="w",
            image=self._get_icon("practice")
        )
        self.day_button.grid(row=1, column=0, pady=8, sticky="ew")

        self.calendar_button = ctk.CTkButton(
            left_panel,
            text="Kalendarz",
            command=self.show_calendar,
            height=50,
            width=button_width,
            font=("Arial", 15),
            fg_color="#8E44AD",
            hover_color="#7D3C98",
            corner_radius=10,
            border_spacing=10,
            anchor="w",
            image=self._get_icon("calendar")
        )
        self.calendar_button.grid(row=2, column=0, pady=8, sticky="ew")

        # Move metronome button to the left section
        self.metronome_button = ctk.CTkButton(
            left_panel,
            text="Metronom",
            command=self.show_metronome,
            height=50,
            width=button_width,
            font=("Arial", 15),
            fg_color="#3498DB",
            hover_color="#2980B9",
            corner_radius=10,
            border_spacing=10,
            anchor="w",
            image=self._get_icon("metronome")
        )
        self.metronome_button.grid(row=3, column=0, pady=8, sticky="ew")

        ctk.CTkLabel(
            right_panel,
            text="Materiały do nauki",
            font=("Arial", 18, "bold"),
            anchor="w"
        ).grid(row=0, column=0, sticky="ew", pady=(0, 15))

        self.theory_button = ctk.CTkButton(
            right_panel,
            text="Teoria muzyki",
            command=self.show_theory,
            height=50,
            width=button_width,
            font=("Arial", 15),
            fg_color="#F1C40F",
            hover_color="#D4AC0D",
            corner_radius=10,
            border_spacing=10,
            anchor="w",
            image=self._get_icon("theory")
        )
        self.theory_button.grid(row=1, column=0, pady=8, sticky="ew")

        self.quiz_button = ctk.CTkButton(
            right_panel,
            text="Quizy muzyczne",
            command=self.show_quiz,
            height=50,
            width=button_width,
            font=("Arial", 15),
            fg_color="#1ABC9C",
            hover_color="#16A085",
            corner_radius=10,
            border_spacing=10,
            anchor="w",
            image=self._get_icon("quiz")
        )
        self.quiz_button.grid(row=2, column=0, pady=8, sticky="ew")

        bottom_frame = ctk.CTkFrame(self.menu_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=60, pady=(20, 30))

        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=0)
        bottom_frame.columnconfigure(2, weight=1)
        bottom_frame.columnconfigure(3, weight=0)
        bottom_frame.columnconfigure(4, weight=1)

        self.settings_button = ctk.CTkButton(
            bottom_frame,
            text="Ustawienia",
            command=self.show_settings,
            width=150,
            height=40,
            font=("Arial", 14),
            fg_color="#8E44AD",
            hover_color="#7D3C98",
            image=self._get_icon("settings")
        )
        self.settings_button.grid(row=0, column=1, padx=10)

        self.quit_button = ctk.CTkButton(
            bottom_frame,
            text="Wyjdź",
            command=master.quit,
            width=150,
            height=40,
            font=("Arial", 14),
            fg_color="#D35B58",
            hover_color="#C77C78",
            image=self._get_icon("quit")
        )
        self.quit_button.grid(row=0, column=3, padx=10)

        # View references
        self.calendar_view = None
        self.day_view = None
        self.settings_view = None
        self.theory_view = None
        self.quiz_view = None
        self.metronome_view = None

        # Frame references
        self.calendar_frame = None
        self.day_frame = None
        self.settings_frame = None
        self.theory_frame = None
        self.quiz_frame = None
        self.metronome_frame = None

    def _get_icon(self, name):
        """Load icon by name if exists"""
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                     "assets", "icons", f"{name}.png")
            return ctk.CTkImage(light_image=Image.open(icon_path), size=(20, 20))
        except:
            return None

    def _hide_all_frames(self):
        self.menu_frame.pack_forget()

        if self.metronome_view and isinstance(self.metronome_view, MetronomeView):
            self.metronome_view.stop_metronome_thread()

        frame_references = [
            (self.calendar_frame, 'calendar_frame', 'calendar_view'),
            (self.day_frame, 'day_frame', 'day_view'),
            (self.settings_frame, 'settings_frame', 'settings_view'),
            (self.theory_frame, 'theory_frame', 'theory_view'),
            (self.quiz_frame, 'quiz_frame', 'quiz_view'),
            (self.metronome_frame, 'metronome_frame', 'metronome_view'),
        ]

        for frame_ref, frame_attr, view_attr in frame_references:
            if frame_ref:
                if frame_ref.winfo_ismapped():
                    frame_ref.pack_forget()
                frame_ref.destroy()

            setattr(self, frame_attr, None)
            setattr(self, view_attr, None)

    def show_menu(self):
        """Return to main menu"""
        self._hide_all_frames()
        self.menu_frame.pack(fill="both", expand=True)

    def show_calendar(self):
        self._hide_all_frames()
        if self.calendar_frame is None:
            self.calendar_frame, self.calendar_view = self._create_view_frame(CalendarView)
        self.calendar_frame.pack(fill="both", expand=True)

    def show_metronome(self):
        """Open metronome view"""
        self._hide_all_frames()
        self.metronome_frame, self.metronome_view = self._create_view_frame(MetronomeView)
        self.metronome_frame.pack(fill="both", expand=True)

    def show_day(self, selected_date=None):
        """Show day view with optional specific date."""
        self._hide_all_frames()
        # Always create a new frame to ensure proper date is passed
        self.day_frame, self.day_view = self._create_day_frame(selected_date)
        self.day_frame.pack(fill="both", expand=True)

    def show_settings(self):
        self._hide_all_frames()
        if self.settings_frame is None:
            self.settings_frame, self.settings_view = self._create_view_frame(SettingsView)
        self.settings_frame.pack(fill="both", expand=True)

    def show_theory(self):
        self._hide_all_frames()
        if self.theory_frame is None:
            self.theory_frame, self.theory_view = self._create_view_frame(TheoryView)
        self.theory_frame.pack(fill="both", expand=True)

    def show_quiz(self):
        self._hide_all_frames()
        if self.quiz_frame is None:
            self.quiz_frame, self.quiz_view = self._create_view_frame(QuizView)
        self.quiz_frame.pack(fill="both", expand=True)

    def _create_view_frame(self, ViewClass):
        """Create frame with back button and target view"""
        frame = ctk.CTkFrame(self.container)

        # Calendar gets special treatment with integrated header
        if ViewClass == CalendarView:
            view = ViewClass(frame, show_day_callback=self.show_day_view, back_callback=self.show_menu)
            view.pack(fill="both", expand=True)
        else:
            top_bar = ctk.CTkFrame(frame, fg_color="transparent", height=50)
            top_bar.pack(fill="x", pady=(10, 0), padx=10)
            top_bar.pack_propagate(False)

            back_button = ctk.CTkButton(
                top_bar,
                text="← Powrót",
                command=self.show_menu,
                width=100,
                height=35,
                fg_color="#555555",
                hover_color="#777777"
            )
            back_button.pack(side="left", pady=5)

            view = ViewClass(frame)
            view.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        return frame, view
    
    def _create_day_frame(self, selected_date=None):
        """Create day view frame with integrated header and callbacks."""
        frame = ctk.CTkFrame(self.container)
        view = DayView(
            frame,
            back_to_menu_callback=self.show_menu,
            back_to_calendar_callback=self.show_calendar,
            selected_date=selected_date
        )
        view.pack(fill="both", expand=True)
        return frame, view
    
    def show_day_view(self, selected_date=None):
        """Show day view, optionally with a specific date selected."""
        self.show_day(selected_date)


def create_main_screen():
    root = ctk.CTk()
    main_screen = MainScreen(root)
    root.mainloop()


if __name__ == "__main__":
    create_main_screen()
