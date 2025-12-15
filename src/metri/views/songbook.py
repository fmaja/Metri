import customtkinter as ctk
from typing import List, Dict, Callable, Optional
import os
import sys
import re

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ..logic.song_func import (
    load_songs, save_songs, get_song, get_new_song,
    song_create, song_edit, remove_song, filter_songs, get_tags
)
from ..logic.display_func import (
    get_display, get_display_lyrics, get_display_chords, get_display_2
)


class SongbookView(ctk.CTkFrame):
    """Songbook view with search, filters, and song management."""

    # White with pistachio color scheme
    ACCENT_PISTACHIO_DARK = "#93C572"
    ACCENT_PISTACHIO_LIGHT = "#B8D8A0"
    BG_LIGHT = "#F0F0F0"
    BG_DARK = "#F8F8F8"
    CARD_BG = "#FFFFFF"
    CARD_BG_DARK = "#F5F5F5"
    TEXT_MUTED = "#7f8c8d"
    HEADER_BG = "#FFFFFF"

    LEFT_PANEL_WIDTH = 320
    OUTER_PADDING = 24
    CARD_GAP = 12
    ACTION_BUTTON_WIDTH = 70

    def __init__(self, master, sidebar=None, back_callback=None, show_module_callback=None, show_menu_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.sidebar = sidebar
        self.back_callback = back_callback
        self._show_module = show_module_callback
        self.show_menu = show_menu_callback
        self.configure(
            fg_color=self.BG_LIGHT if ctk.get_appearance_mode() == "Light" else self.BG_DARK
        )

        # Data storage
        self.songs_data: List[Dict] = []
        self.filtered_songs: List[Dict] = []
        self.selected_songs: List[int] = []  # song IDs of selected songs

        # UI References
        self.song_widgets: List[Dict] = []
        self.search_var = ctk.StringVar()
        self._search_timer = None
        self.search_var.trace_add("write", lambda *args: self._debounced_search())
        self.language_var = ctk.StringVar(value="Wszystkie")
        self.sort_var = ctk.StringVar(value="Tytuł (A-Z)")
        
        # Tag checkboxes
        self.tag_vars = {}

        # View state
        self.current_mode: str = "list"  # list | form | display
        self.current_form_song_id: Optional[int] = None
        self.current_display_song_id: Optional[int] = None
        self.display_view_mode: int = 0  # 0=chords side-by-side, 1=chords inline
        self.songs_scroll = None
        self.delete_btn = None
        self.select_all_btn = None
        self.form_widgets: Dict[str, object] = {}
        self.form_error_label = None
        self.display_widgets: Dict[str, object] = {}
        self.left_frame = None
        self.right_frame = None
        self.right_header = None
        self.right_content = None
        
        # Performance cache
        self._color_cache = {}
        self._song_render_job = None
        self._render_batch_size = 12
        self._render_index = 0
        self._list_loading_label = None
        self._last_filter_signature = None

        # Load songs data
        self._load_songs()

        # Build UI
        self._build_ui()

    def _load_songs(self):
        """Load songs from JSON file using song_func."""
        try:
            self.songs_data = load_songs()
            self.filtered_songs = self.songs_data.copy()
        except Exception as e:
            print(f"Error loading songbook data: {e}")
            self.songs_data = []
            self.filtered_songs = []

    def _save_songs(self):
        """Save songs to JSON file using song_func."""
        try:
            save_songs(self.songs_data)
        except Exception as e:
            print(f"Error saving songbook data: {e}")

    def _build_ui(self):
        """Build the main UI structure."""
        # Configure grid - left column 20%, right column 80% with uniform sizing
        self.grid_columnconfigure(0, weight=1, uniform="col_unit")
        self.grid_columnconfigure(1, weight=4, uniform="col_unit")
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # Header bar
        self._create_header()

        # Left panel - Options
        self._create_left_panel()

        # Right panel - Song list
        self._create_right_panel()

    def _create_header(self):
        """Create the header bar with back button and title."""
        header = ctk.CTkFrame(self, fg_color=self.HEADER_BG, height=72, corner_radius=12)
        header.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=20,
            pady=(20, 20)
        )
        header.grid_propagate(False)

        # Back button
        back_btn = ctk.CTkButton(
            header,
            text="←",
            command=self._on_back,
            width=44,
            height=44,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            text_color="#FFFFFF",
            corner_radius=12
        )
        back_btn.pack(side="left", padx=(18, 10), pady=16)

        # Title
        title_label = ctk.CTkLabel(
            header,
            text="Śpiewnik",
            font=ctk.CTkFont(size=40, weight="bold"),
            text_color=self.ACCENT_PISTACHIO_DARK
        )
        title_label.pack(side="left", padx=(10, 0), pady=16)

        # Store header reference for dynamic buttons
        self.header_frame = header
        
        # Add new song button
        self.add_btn = ctk.CTkButton(
            header,
            text="Dodaj piosenkę",
            command=self._add_new_song,
            width=180,
            height=40,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF",
            corner_radius=10
        )
        self.add_btn.pack(side="right", padx=(0, 18), pady=16)
        
        # Back to list button (hidden by default)
        self.back_to_list_btn = ctk.CTkButton(
            header,
            text="Wróć do listy",
            command=self._handle_form_cancel,
            width=150,
            height=40,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 14, "bold"),
            text_color="#FFFFFF",
            corner_radius=10
        )
        # Don't pack it yet - will be shown when needed
        
        # Display back button (for display view)
        self.display_back_btn = ctk.CTkButton(
            header,
            text="←",
            command=self._handle_display_back,
            width=50,
            height=40,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 20, "bold"),
            text_color="#FFFFFF",
            corner_radius=10
        )
        # Don't pack it yet - will be shown when needed
        
        # Form back button (for form view)
        self.form_back_btn = ctk.CTkButton(
            header,
            text="←",
            command=self._handle_form_cancel,
            width=50,
            height=40,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 20, "bold"),
            text_color="#FFFFFF",
            corner_radius=10
        )
        # Don't pack it yet - will be shown when needed

    def _create_left_panel(self):
        """Create the left panel with search and filters."""
        self.left_frame = ctk.CTkFrame(self, fg_color=self.CARD_BG, corner_radius=12)
        self.left_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(20, 10),
            pady=(0, 20)
        )
        self._render_filter_controls()

    def _render_filter_controls(self):
        if not self.left_frame:
            return

        for widget in self.left_frame.winfo_children():
            widget.destroy()

        left_frame = self.left_frame
        inner_pad = 20

        # Filters at top
        ctk.CTkLabel(
            left_frame,
            text="Wyszukaj:",
            font=("Roboto", 16, "bold"),
            anchor="w"
        ).pack(pady=(20, 6), padx=inner_pad, anchor="w")

        search_entry = ctk.CTkEntry(
            left_frame,
            textvariable=self.search_var,
            placeholder_text="Wpisz tytuł lub wykonawcę...",
            height=40,
            font=("Roboto", 14),
            corner_radius=10
        )
        search_entry.pack(pady=(0, 20), padx=inner_pad, fill="x")

        ctk.CTkLabel(
            left_frame,
            text="Język:",
            font=("Roboto", 16, "bold"),
            anchor="w"
        ).pack(pady=(10, 5), padx=inner_pad, anchor="w")

        languages = ["Wszystkie", "Polski", "Angielski", "Niemiecki", "Inny"]
        language_menu = ctk.CTkOptionMenu(
            left_frame,
            variable=self.language_var,
            values=languages,
            command=lambda _: self._apply_filters(),
            height=40,
            font=("Roboto", 14),
            fg_color=self.ACCENT_PISTACHIO_DARK,
            button_color=self.ACCENT_PISTACHIO_DARK,
            button_hover_color="#7FAD5A",
            text_color="#FFFFFF",
            corner_radius=10
        )
        language_menu.pack(pady=(0, 20), padx=inner_pad, fill="x")

        ctk.CTkLabel(
            left_frame,
            text="Tagi:",
            font=("Roboto", 16, "bold"),
            anchor="w"
        ).pack(pady=(10, 5), padx=inner_pad, anchor="w")

        # Get all tags
        try:
            all_tags = get_tags()
        except:
            all_tags = set()
            for song in self.songs_data:
                all_tags.update(song.get("tags", []))
        
        tag_values = ["Wszystkie"] + sorted(list(all_tags))
        if not hasattr(self, 'tag_var'):
            self.tag_var = ctk.StringVar(value="Wszystkie")
        
        tag_menu = ctk.CTkOptionMenu(
            left_frame,
            variable=self.tag_var,
            values=tag_values,
            command=lambda _: self._apply_filters(),
            height=40,
            font=("Roboto", 14),
            fg_color=self.ACCENT_PISTACHIO_DARK,
            button_color=self.ACCENT_PISTACHIO_DARK,
            button_hover_color="#7FAD5A",
            text_color="#FFFFFF",
            corner_radius=10
        )
        tag_menu.pack(pady=(0, 20), padx=inner_pad, fill="x")

        ctk.CTkLabel(
            left_frame,
            text="Sortuj według:",
            font=("Roboto", 16, "bold"),
            anchor="w"
        ).pack(pady=(10, 5), padx=inner_pad, anchor="w")

        sort_options = [
            "Tytuł (A-Z)",
            "Tytuł (Z-A)",
            "Wykonawca (A-Z)",
            "Wykonawca (Z-A)",
            "ID (rosnąco)",
            "ID (malejąco)"
        ]
        sort_menu = ctk.CTkOptionMenu(
            left_frame,
            variable=self.sort_var,
            values=sort_options,
            command=lambda _: self._apply_filters(),
            height=40,
            font=("Roboto", 14),
            fg_color=self.ACCENT_PISTACHIO_DARK,
            button_color=self.ACCENT_PISTACHIO_DARK,
            button_hover_color="#7FAD5A",
            text_color="#FFFFFF",
            corner_radius=10
        )
        sort_menu.pack(pady=(0, 20), padx=inner_pad, fill="x")

        # Spacer to push buttons to bottom
        ctk.CTkFrame(left_frame, fg_color="transparent", height=20).pack(fill="both", expand=True)

        # Action buttons at bottom
        self.select_all_btn = ctk.CTkButton(
            left_frame,
            text="Zaznacz wszystkie",
            command=self._toggle_select_all,
            height=40,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 14, "bold"),
            text_color="#FFFFFF",
            corner_radius=10
        )
        self.select_all_btn.pack(pady=(10, 10), padx=inner_pad, fill="x")

        self.delete_btn = ctk.CTkButton(
            left_frame,
            text="Usuń zaznaczone",
            command=self._delete_selected_songs,
            height=40,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 14, "bold"),
            text_color="#FFFFFF",
            corner_radius=10,
            state="disabled"
        )
        self.delete_btn.pack(pady=(0, 20), padx=inner_pad, fill="x")

    def _update_tag_checkboxes(self):
        """Update the tag checkboxes based on available tags."""
        frame = getattr(self, "tags_frame", None)
        if not frame:
            return
        try:
            if not frame.winfo_exists():
                return
        except Exception:
            return
        # Clear existing checkboxes
        for widget in frame.winfo_children():
            widget.destroy()

        # Get all unique tags using get_tags function
        try:
            all_tags = get_tags()
        except:
            all_tags = set()
            for song in self.songs_data:
                all_tags.update(song.get("tags", []))

        # Create checkboxes
        self.tag_vars = {}
        for tag in sorted(all_tags):
            var = ctk.BooleanVar(value=False)
            self.tag_vars[tag] = var
            checkbox = ctk.CTkCheckBox(
                frame,
                text=tag,
                variable=var,
                command=self._apply_filters,
                font=("Roboto", 13),
                fg_color=self.ACCENT_PISTACHIO_DARK,
                hover_color=self._get_darker_color(self.ACCENT_PISTACHIO_DARK),
                corner_radius=5
            )
            checkbox.pack(anchor="w", pady=3)

        if not all_tags:
            ctk.CTkLabel(
                frame,
                text="Brak tagów",
                font=("Roboto", 13),
                text_color=self.TEXT_MUTED
            ).pack(anchor="w")

    def _create_right_panel(self):
        """Create the right panel container that swaps between list and form views."""
        self.right_frame = ctk.CTkFrame(self, fg_color=self.CARD_BG, corner_radius=12)
        self.right_frame.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=(10, 20),
            pady=(0, 20)
        )

        self.right_header = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.right_header.pack(fill="x", pady=(20, 10), padx=self.OUTER_PADDING)

        self.right_content = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.right_content.pack(fill="both", expand=True, padx=self.OUTER_PADDING, pady=(10, 20))

        self._render_right_panel()

    def _clear_frame(self, frame: Optional[ctk.CTkFrame]):
        """Remove all children from a frame."""
        if not frame:
            return
        for widget in frame.winfo_children():
            widget.destroy()

    def _render_right_panel(self):
        """Render the right panel content based on the current mode."""
        self._clear_frame(self.right_header)
        self._clear_frame(self.right_content)

        if self.current_mode == "form":
            self._render_form_view()
        elif self.current_mode == "display":
            self._render_display_view()
        else:
            self._render_list_view()

    def _render_list_view(self):
        """Show the song list header and content."""
        self.form_widgets = {}
        self.form_error_label = None
        
        # Update header buttons
        self.back_to_list_btn.pack_forget()
        self.display_back_btn.pack_forget()
        self.form_back_btn.pack_forget()
        self.add_btn.pack(side="right", padx=(0, 18), pady=16)

        # Subtle accent line
        accent_line = ctk.CTkFrame(self.right_header, fg_color=self.ACCENT_PISTACHIO_LIGHT, height=3, corner_radius=0)
        accent_line.pack(fill="x", pady=(0, 10))

        title_label = ctk.CTkLabel(
            self.right_header,
            text="Spis treści",
            font=("Roboto", 22, "bold"),
            text_color=self.ACCENT_PISTACHIO_DARK
        )
        title_label.pack(side="left", anchor="w")

        self.songs_scroll = ctk.CTkScrollableFrame(
            self.right_content,
            fg_color="transparent",
            corner_radius=0
        )
        self.songs_scroll.pack(fill="both", expand=True)

        self._refresh_song_list()

    def _refresh_song_list(self):
        """Refresh the song list display."""
        if not self.songs_scroll:
            return

        self._cancel_song_render_job()

        # Clear existing widgets
        for widget in self.songs_scroll.winfo_children():
            widget.destroy()

        self.song_widgets = []
        self.selected_songs = []
        if self._list_loading_label:
            self._list_loading_label = None

        if not self.filtered_songs:
            ctk.CTkLabel(
                self.songs_scroll,
                text="Brak piosenek do wyświetlenia.\nDodaj nowe piosenki używając przycisku '+Dodaj Piosenkę'",
                font=("Roboto", 16),
                text_color=self.TEXT_MUTED,
                justify="center"
            ).pack(pady=50)
            self._update_delete_button_state()
            return

        self._list_loading_label = ctk.CTkLabel(
            self.songs_scroll,
            text="Ładowanie listy…",
            font=("Roboto", 14),
            text_color=self.ACCENT_PISTACHIO_DARK
        )
        self._list_loading_label.pack(pady=20)

        self._render_index = 0
        self._render_song_batch()

    def _cancel_song_render_job(self):
        if self._song_render_job:
            try:
                self.after_cancel(self._song_render_job)
            except Exception:
                pass
            self._song_render_job = None

    def _render_song_batch(self):
        if self.current_mode != "list":
            self._song_render_job = None
            return

        if not self.songs_scroll or not self.songs_scroll.winfo_exists():
            self._song_render_job = None
            return

        if self._render_index == 0 and self._list_loading_label:
            self._list_loading_label.destroy()
            self._list_loading_label = None

        end_index = min(self._render_index + self._render_batch_size, len(self.filtered_songs))

        for idx in range(self._render_index, end_index):
            self._create_song_item(self.filtered_songs[idx])

        self._render_index = end_index

        if self._render_index >= len(self.filtered_songs):
            self._song_render_job = None
            self._update_delete_button_state()
            return

        self._song_render_job = self.after(20, self._render_song_batch)

    def _create_song_item(self, song: Dict):
        """Create a song item in the list."""
        song_id = song['id']
        
        # Song card
        song_frame = ctk.CTkFrame(
            self.songs_scroll,
            fg_color=self._get_card_bg(),
            corner_radius=12,
            border_width=0
        )
        song_frame.pack(fill="x", pady=self.CARD_GAP // 2, padx=self.CARD_GAP)

        # Content frame
        content = ctk.CTkFrame(song_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=self.OUTER_PADDING - 6, pady=14)
        
        # Hover effect - single bind to main frame
        song_frame.bind("<Enter>", lambda e: song_frame.configure(fg_color=self._get_card_hover_bg()))
        song_frame.bind("<Leave>", lambda e: song_frame.configure(fg_color=self._get_card_bg()))

        # Song info
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        # Make info_frame clickable to view song
        info_frame.bind("<Button-1>", lambda e, sid=song_id: self._view_song(sid))
        info_frame.configure(cursor="hand2")

        # Single-line: Title - Artist - Group only
        title_text = song.get("title", "Bez tytułu")
        artist_text = song.get("artist", "")
        group_text = song.get("group", "")
        
        parts = [title_text]
        if artist_text:
            parts.append(artist_text)
        if group_text:
            parts.append(group_text)
        
        combined_text = "  —  ".join(parts)
        
        combined_label = ctk.CTkLabel(
            info_frame,
            text=combined_text,
            font=("Roboto", 16),
            anchor="w",
            cursor="hand2"
        )
        combined_label.pack(anchor="w")
        combined_label.bind("<Button-1>", lambda e, sid=song_id: self._view_song(sid))

        actions_frame = ctk.CTkFrame(content, fg_color="transparent")
        actions_frame.pack(side="right", padx=(12, 0))

        checkbox_var = ctk.BooleanVar(value=False)
        checkbox = ctk.CTkCheckBox(
            actions_frame,
            text="",
            variable=checkbox_var,
            command=lambda sid=song_id, v=checkbox_var: self._on_song_select(sid, v),
            width=20,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            corner_radius=5
        )
        checkbox.pack(side="left", padx=(0, 10))

        # Icon buttons - square
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑",
            command=lambda sid=song_id: self._delete_single_song(sid),
            width=36,
            height=36,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 16),
            text_color="#FFFFFF",
            corner_radius=8
        )
        delete_btn.pack(side="left", padx=(0, 8))

        edit_btn = ctk.CTkButton(
            actions_frame,
            text="✏",
            command=lambda sid=song_id: self._edit_song(sid),
            width=36,
            height=36,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 16),
            text_color="#FFFFFF",
            corner_radius=8
        )
        edit_btn.pack(side="left")

        # Store references
        self.song_widgets.append({
            "frame": song_frame,
            "checkbox_var": checkbox_var,
            "checkbox": checkbox,
            "song_id": song_id
        })

    def _on_song_select(self, song_id: int, var: ctk.BooleanVar):
        """Handle song selection."""
        if var.get():
            if song_id not in self.selected_songs:
                self.selected_songs.append(song_id)
        else:
            if song_id in self.selected_songs:
                self.selected_songs.remove(song_id)

        self._update_delete_button_state()

    def _update_delete_button_state(self):
        """Enable/disable delete button based on selection."""
        if not self.delete_btn:
            return

        if self.selected_songs:
            self.delete_btn.configure(state="normal")
        else:
            self.delete_btn.configure(state="disabled")

    def _toggle_select_all(self):
        """Toggle selection of all songs."""
        if not self.filtered_songs or not self.select_all_btn:
            return

        # Check if all are selected
        all_selected = len(self.selected_songs) == len(self.filtered_songs)

        if all_selected:
            # Deselect all
            self.selected_songs = []
            for widget in self.song_widgets:
                widget["checkbox_var"].set(False)
            self.select_all_btn.configure(text="Zaznacz wszystkie")
        else:
            # Select all
            self.selected_songs = [song['id'] for song in self.filtered_songs]
            for widget in self.song_widgets:
                widget["checkbox_var"].set(True)
            self.select_all_btn.configure(text="Odznacz wszystkie")

        self._update_delete_button_state()

    def _delete_selected_songs(self):
        """Delete selected songs after confirmation."""
        if not self.selected_songs:
            return

        # Confirmation dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Potwierdzenie")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text=f"Czy na pewno chcesz usunąć\n{len(self.selected_songs)} piosenek?",
            font=("Roboto", 16),
            justify="center"
        ).pack(pady=30)

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=10)

        ctk.CTkButton(
            button_frame,
            text="Anuluj",
            command=dialog.destroy,
            width=120,
            height=40,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 14),
            corner_radius=10,
            text_color="#FFFFFF"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="Usuń",
            command=lambda: self._confirm_delete(dialog),
            width=120,
            height=40,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 14, "bold"),
            corner_radius=10,
            text_color="#FFFFFF"
        ).pack(side="left", padx=10)

    def _delete_single_song(self, song_id: int):
        """Prompt deletion for a single song from the row controls."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Usuń piosenkę")
        dialog.geometry("380x180")
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text="Czy na pewno chcesz usunąć tę piosenkę?",
            font=("Roboto", 16),
            justify="center"
        ).pack(pady=28)

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=10)

        ctk.CTkButton(
            button_frame,
            text="Anuluj",
            command=dialog.destroy,
            width=120,
            height=40,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 14),
            corner_radius=10,
            text_color="#FFFFFF"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="Usuń",
            command=lambda: self._confirm_single_delete(song_id, dialog),
            width=120,
            height=40,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 14, "bold"),
            corner_radius=10,
            text_color="#FFFFFF"
        ).pack(side="left", padx=10)

    def _confirm_delete(self, dialog):
        """Confirm and execute deletion."""
        # Remove from main data using remove_song
        for song_id in self.selected_songs:
            remove_song(song_id)

        self._refresh_after_delete()
        dialog.destroy()

    def _confirm_single_delete(self, song_id: int, dialog):
        remove_song(song_id)
        self._refresh_after_delete()
        dialog.destroy()

    def _refresh_after_delete(self):
        self.selected_songs = []
        self._load_songs()
        self._apply_filters(force=True)
        self._update_tag_checkboxes()

    def _debounced_search(self):
        """Debounce search input to avoid filtering on every keystroke."""
        if self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, self._apply_filters)  # 300ms delay

    def _apply_filters(self, force: bool = False):
        """Apply filters; skip work if inputs unchanged unless force=True."""
        search_text = self.search_var.get().lower()
        language_filter = self.language_var.get()


        
        # Build search args for filter_songs
        search_args = {}

        selected_tag = self.tag_var.get()
        if selected_tag != "Wszystkie":
            search_args['tags'] = [selected_tag]

        if search_text:
            search_args['search'] = search_text
        
        if language_filter != "Wszystkie":
            search_args['language'] = language_filter
        

        
        # Sort
        sort_option = self.sort_var.get()
        if sort_option == "Tytuł (A-Z)":
            search_args['filter_by'] = 'title'
            search_args['order'] = 'asc'
        elif sort_option == "Tytuł (Z-A)":
            search_args['filter_by'] = 'title'
            search_args['order'] = 'desc'
        elif sort_option == "Wykonawca (A-Z)":
            search_args['filter_by'] = 'artist'
            search_args['order'] = 'asc'
        elif sort_option == "Wykonawca (Z-A)":
            search_args['filter_by'] = 'artist'
            search_args['order'] = 'desc'
        elif sort_option == "ID (rosnąco)":
            search_args['filter_by'] = 'id'
            search_args['order'] = 'asc'
        elif sort_option == "ID (malejąco)":
            search_args['filter_by'] = 'id'
            search_args['order'] = 'desc'

        signature = (
            search_text,
            language_filter,
            tuple(sorted(selected_tag)),
            sort_option,
        )

        if not force and signature == self._last_filter_signature:
            return
        self._last_filter_signature = signature

        try:
            self.filtered_songs = filter_songs(search_args)
        except:
            # Fallback to manual filtering
            self.filtered_songs = self.songs_data.copy()
        
        if self.current_mode == "list" and self.songs_scroll:
            self._refresh_song_list()

    def _add_new_song(self):
        """Switch to inline form for creating a new song."""
        self._open_form()

    def _edit_song(self, song_id: int):
        """Switch to inline form for editing an existing song."""
        song = get_song(song_id)
        if song:
            self._open_form(song_id)

    def _open_form(self, song_id: Optional[int] = None):
        """Update state and render form view."""
        self.current_display_song_id = None
        self.current_form_song_id = song_id
        self.current_mode = "form"
        self._render_right_panel()

    def _render_form_view(self):
        """Render the inline form for adding or editing a song."""
        is_edit = self.current_form_song_id is not None
        form_title = "Edytuj piosenkę" if is_edit else "Nowa piosenka"
        self.songs_scroll = None
        self.delete_btn = None
        self.select_all_btn = None
        
        # Update header buttons - use arrow for form
        self.add_btn.pack_forget()
        self.display_back_btn.pack_forget()
        self.back_to_list_btn.pack_forget()
        self.form_back_btn.pack_forget()
        
        self.form_back_btn.pack(side="right", padx=(0, 18), pady=16)

        # Subtle accent line
        accent_line = ctk.CTkFrame(self.right_header, fg_color=self.ACCENT_PISTACHIO_LIGHT, height=3, corner_radius=0)
        accent_line.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            self.right_header,
            text=form_title,
            font=("Roboto", 20, "bold"),
            text_color=self.ACCENT_PISTACHIO_DARK
        ).pack(side="left", anchor="w")

        initial_data = self._get_form_initial_data()
        self.form_widgets = {}

        self._populate_left_panel_for_form(initial_data, is_edit)

        form_body = ctk.CTkFrame(self.right_content, fg_color="transparent")
        form_body.pack(fill="both", expand=True, padx=10, pady=10)

        if is_edit:
            text_container = ctk.CTkFrame(form_body, fg_color="transparent")
            text_container.pack(fill="both", expand=True, pady=(10, 10))
            text_container.grid_columnconfigure(0, weight=1)
            text_container.grid_columnconfigure(1, weight=1)
            text_container.grid_rowconfigure(0, weight=1)

            lyrics_frame = ctk.CTkFrame(text_container, fg_color="transparent")
            lyrics_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

            chords_frame = ctk.CTkFrame(text_container, fg_color="transparent")
            chords_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

            # Lyrics label with tooltip
            lyrics_label_frame = ctk.CTkFrame(lyrics_frame, fg_color="transparent")
            lyrics_label_frame.pack(anchor="w", pady=(0, 8))
            
            ctk.CTkLabel(
                lyrics_label_frame,
                text="Tekst",
                font=("Roboto", 14, "bold")
            ).pack(side="left")
            
            lyrics_tooltip = ctk.CTkLabel(
                lyrics_label_frame,
                text=" ⓘ",
                font=("Roboto", 14),
                text_color=self.ACCENT_PISTACHIO_DARK,
                cursor="hand2"
            )
            lyrics_tooltip.pack(side="left", padx=(5, 0))
            self._show_tooltip(lyrics_tooltip, "Tekst piosenki podzielony na sekcje. Format:\n[v1] - zwrotka 1\n[c1] - refren 1\n[i1] - intro/instrumentalka\n\nKażda sekcja zaczyna się od nawiasu kwadratowego. Zachowaj kolejność sekcji zgodną z przebiegiem utworu.")

            lyrics_box = ctk.CTkTextbox(lyrics_frame, font=("Roboto", 12), wrap="word")
            lyrics_box.pack(fill="both", expand=True)
            lyrics_box.insert("1.0", initial_data.get("lyrics", ""))
            self.form_widgets["lyrics"] = lyrics_box

            # Chords label with tooltip
            chords_label_frame = ctk.CTkFrame(chords_frame, fg_color="transparent")
            chords_label_frame.pack(anchor="w", pady=(0, 8))
            
            ctk.CTkLabel(
                chords_label_frame,
                text="Akordy",
                font=("Roboto", 14, "bold")
            ).pack(side="left")
            
            chords_tooltip = ctk.CTkLabel(
                chords_label_frame,
                text=" ⓘ",
                font=("Roboto", 14),
                text_color=self.ACCENT_PISTACHIO_DARK,
                cursor="hand2"
            )
            chords_tooltip.pack(side="left", padx=(5, 0))
            self._show_tooltip(chords_tooltip, "Akordy dla każdej sekcji. Format jak w tekście:\n[v1]\nC G Am F\n[c1]\nF C G C\n\nKażda sekcja musi mieć taką samą nazwę jak w tekście. Akordy są wyświetlane nad odpowiednimi wersami w tekście.")

            chords_box = ctk.CTkTextbox(chords_frame, font=("Roboto", 12), wrap="word")
            chords_box.pack(fill="both", expand=True)
            chords_box.insert("1.0", initial_data.get("chords", ""))
            self.form_widgets["chords"] = chords_box
        else:
            ctk.CTkLabel(
                form_body,
                text="Tekst piosenki z akordami:",
                font=("Roboto", 14, "bold")
            ).pack(anchor="w", pady=(16, 4))
            ctk.CTkLabel(
                form_body,
                text="Wklej cały tekst wraz z akordami (jeden blok). Program sam rozpozna strukturę.",
                font=("Roboto", 11),
                text_color=self.TEXT_MUTED
            ).pack(anchor="w", pady=(0, 6))

            combined_box = ctk.CTkTextbox(form_body, height=320, font=("Roboto", 12))
            combined_box.pack(fill="both", expand=False, pady=(0, 10))
            self.form_widgets["combined_content"] = combined_box

        action_bar = ctk.CTkFrame(self.right_content, fg_color=self.CARD_BG, height=80, corner_radius=10)
        action_bar.pack(fill="x", pady=(15, 0))
        action_bar.pack_propagate(False)

        self.form_error_label = ctk.CTkLabel(
            action_bar,
            text="",
            font=("Roboto", 12),
            text_color=self.ACCENT_PISTACHIO_LIGHT
        )
        self.form_error_label.pack(side="left", padx=20)

        btn_frame = ctk.CTkFrame(action_bar, fg_color="transparent")
        btn_frame.pack(side="right", padx=20)

        ctk.CTkButton(
            btn_frame,
            text="Anuluj",
            command=self._handle_form_cancel,
            width=130,
            height=45,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 14),
            text_color="#FFFFFF",
            corner_radius=10
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame,
            text="Zapisz",
            command=self._save_form_data,
            width=150,
            height=45,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 14, "bold"),
            text_color="#FFFFFF",
            corner_radius=10
        ).pack(side="left", padx=8)

    def _render_display_view(self):
        """Render the inline song preview with transpose controls."""
        self.songs_scroll = None
        self.delete_btn = None
        self.select_all_btn = None
        
        # Update header buttons
        self.add_btn.pack_forget()
        self.back_to_list_btn.pack_forget()
        self.form_back_btn.pack_forget()
        self.display_back_btn.pack(side="right", padx=(0, 18), pady=16)

        song_id = self.current_display_song_id
        song = get_song(song_id) if song_id is not None else None

        if not song:
            ctk.CTkLabel(
                self.right_header,
                text="Piosenka nie została znaleziona",
                font=("Roboto", 18, "bold"),
                text_color=self.ACCENT_PISTACHIO_LIGHT
            ).pack(side="left")

            ctk.CTkButton(
                self.right_header,
                text="Wróć",
                command=self._handle_display_back,
                width=140,
                height=40,
                fg_color=self.ACCENT_PISTACHIO_DARK,
                hover_color="#7FAD5A",
                font=("Roboto", 14, "bold"),
                text_color="#FFFFFF",
                corner_radius=10
            ).pack(side="right")
            return

        self.display_widgets = {"song": song}

        # First row: Title and Artist
        title_row = ctk.CTkFrame(self.right_header, fg_color="transparent")
        title_row.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(
            title_row,
            text=song.get("title", "Bez tytułu"),
            font=("Roboto", 22, "bold"),
            text_color=self.ACCENT_PISTACHIO_DARK,
            anchor="w"
        ).pack(side="left", anchor="w")
        
        # Artist - Group on the right side
        artist = song.get("artist", "")
        group = song.get("group", "")
        artist_group_parts = []
        if artist:
            artist_group_parts.append(artist)
        if group:
            artist_group_parts.append(group)
        if artist_group_parts:
            ctk.CTkLabel(
                title_row,
                text=" - ".join(artist_group_parts),
                font=("Roboto", 15),
                text_color=self.TEXT_MUTED
            ).pack(side="right", padx=(20, 0))
        
        # Subtle accent line below title
        accent_line = ctk.CTkFrame(self.right_header, fg_color=self.ACCENT_PISTACHIO_LIGHT, height=3, corner_radius=0)
        accent_line.pack(fill="x", pady=(5, 5))
        
        # Key, Capo, Meter info line (left-aligned below line)
        capo_val = song.get("capo") or "-"
        key_val = song.get("key") or "-"
        meter_val = song.get("meter") or "-"
        info_text = f"K: {capo_val}   T: {key_val}   M: {meter_val}"
        
        ctk.CTkLabel(
            self.right_header,
            text=info_text,
            font=("Roboto", 13),
            text_color="#000000",
            anchor="w"
        ).pack(anchor="w")

        self._populate_left_panel_for_display(song_id)

        view_switch = self.display_widgets.get("view_switch")

        scroll = ctk.CTkScrollableFrame(self.right_content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self.display_widgets["view_switch"] = view_switch
        self.display_widgets["scroll"] = scroll

        self._render_display_text()

    def _populate_left_panel_for_display(self, song_id: int):
        """Replace left panel content with display controls."""
        if not self.left_frame:
            return

        for widget in self.left_frame.winfo_children():
            widget.destroy()

        ctk.CTkButton(
            self.left_frame,
            text="Edytuj piosenkę",
            command=lambda: self._open_form(song_id),
            height=45,
            fg_color=self.ACCENT_PISTACHIO_DARK,
            hover_color="#7FAD5A",
            font=("Roboto", 14, "bold"),
            text_color="#FFFFFF",
            corner_radius=10
        ).pack(pady=(20, 20), padx=20, fill="x")

        ctk.CTkLabel(
            self.left_frame,
            text="Tryb wyświetlania:",
            font=("Roboto", 16, "bold"),
            anchor="w"
        ).pack(pady=(10, 5), padx=20, anchor="w")

        view_switch = ctk.CTkSwitch(
            self.left_frame,
            text="Akordy obok tekstu",
            command=self._toggle_display_view,
            font=("Roboto", 14),
            fg_color=self.ACCENT_PISTACHIO_DARK,
            progress_color=self.ACCENT_PISTACHIO_LIGHT
        )
        view_switch.pack(pady=(5, 20), padx=20, anchor="w")
        if self.display_view_mode == 0:
            view_switch.select()
        else:
            view_switch.deselect()

        self.display_widgets["view_switch"] = view_switch

    def _render_display_text(self):
        """Draw the song text with chords using the display helper."""
        scroll = self.display_widgets.get("scroll")
        if not scroll or not self.current_display_song_id:
            return

        for widget in scroll.winfo_children():
            widget.destroy()

        try:
            if self.display_view_mode == 0:
                display_data = get_display_2(self.current_display_song_id)
                self._render_side_by_side(scroll, display_data)
            else:
                display_text = get_display(self.current_display_song_id, 0)
                self._parse_display_text(scroll, display_text)
        except Exception as exc:
            ctk.CTkLabel(
                scroll,
                text=f"Błąd wyświetlania piosenki: {exc}",
                font=("Roboto", 13),
                text_color=self.ACCENT_PISTACHIO_LIGHT
            ).pack(pady=20)

    def _render_side_by_side(self, parent, display_data):
        """Render lyrics and chords side by side in two columns within the main scroll."""
        if not display_data or len(display_data) < 2:
            ctk.CTkLabel(
                parent,
                text="Brak danych do wyświetlenia.",
                font=("Roboto", 13),
                text_color=self.ACCENT_PISTACHIO_LIGHT
            ).pack(pady=20)
            return

        lyrics_text = display_data[0]
        chords_text = display_data[1]

        lyrics_lines = lyrics_text.split('\n')
        chords_lines = chords_text.split('\n')

        max_lines = max(len(lyrics_lines), len(chords_lines))

        # Calculate how many columns can fit
        parent.update_idletasks()
        scroll_width = parent.winfo_width()
        lines_per_column = 50  # Max lines per column
        num_columns = 1
        
        if scroll_width > 1200 and max_lines > lines_per_column:
            num_columns = min(2, (max_lines + lines_per_column - 1) // lines_per_column)

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(anchor="w", padx=self.OUTER_PADDING, pady=12)

        font_lyrics = ("Roboto", 17)
        font_chords = ("Roboto", 16, "bold")

        for col_idx in range(num_columns):
            container.grid_columnconfigure(col_idx * 2, weight=0)
            container.grid_columnconfigure(col_idx * 2 + 1, weight=0)

        # Split content into multiple columns
        widget_count = 0
        for col_idx in range(num_columns):
            start_line = col_idx * lines_per_column
            end_line = min(start_line + lines_per_column, max_lines)

            for i in range(start_line, end_line):
                widget_count += 1
                # Update UI periodically to keep responsive
                if widget_count % 20 == 0:
                    self.update_idletasks()
                row = i - start_line
                lyrics_line = lyrics_lines[i] if i < len(lyrics_lines) else ''
                chords_line = chords_lines[i] if i < len(chords_lines) else ''

                if lyrics_line.strip() or chords_line.strip():
                    lyrics_label = ctk.CTkLabel(
                        container,
                        text=lyrics_line if lyrics_line else ' ',
                        font=font_lyrics,
                        anchor="w",
                        justify="left"
                    )
                    lyrics_label.grid(
                        row=row,
                        column=col_idx * 2,
                        sticky="w",
                        padx=(30 if col_idx > 0 else 0, 8),
                        pady=1
                    )

                    chord_label = ctk.CTkLabel(
                        container,
                        text=chords_line if chords_line else ' ',
                        font=font_chords,
                        text_color=self.ACCENT_PISTACHIO_DARK,
                        anchor="w",
                        justify="left"
                    )
                    chord_label.grid(
                        row=row,
                        column=col_idx * 2 + 1,
                        sticky="w",
                        pady=1
                    )
                else:
                    spacer = ctk.CTkLabel(container, text='', height=10)
                    spacer.grid(row=row, column=col_idx * 2, columnspan=2)

    def _parse_display_text(self, parent, display_text: str):
        """Parse the pseudo-HTML markup into CTk labels."""
        paragraphs = display_text.split('\n\n')
        mono_font = ("Courier New", 16)
        chord_font = ("Courier New", 16, "bold")

        for para in paragraphs:
            if not para.strip():
                continue

            para_frame = ctk.CTkFrame(parent, fg_color="transparent")
            para_frame.pack(anchor="w", pady=(0, 18))

            lines = para.strip().split('\n')
            for line in lines:
                if not line.strip():
                    ctk.CTkLabel(para_frame, text="", height=6).pack()
                    continue

                if '<b>' in line:
                    text = re.sub(r'</?b>', '', line)
                    if '<code>' in text:
                        # Check if line starts with tab (chorus chords)
                        has_indent = text.startswith('\t')
                        chord_line = re.sub(r'</?code>', '', text)
                        chord_line = chord_line.replace('\t', '    ')
                        ctk.CTkLabel(
                            para_frame,
                            text=chord_line,
                            font=chord_font,
                            text_color=self.ACCENT_PISTACHIO_DARK,
                            anchor="w",
                            justify="left"
                        ).pack(anchor="w", pady=(0, 0))
                    else:
                        # [i] section chords - lighter color but bold
                        ctk.CTkLabel(
                            para_frame,
                            text=text,
                            font=chord_font,
                            text_color=self.TEXT_MUTED,
                            anchor="w",
                            justify="left"
                        ).pack(anchor="w", pady=(4, 1))
                elif '<i>' in line:
                    text = re.sub(r'</?i>', '', line)
                    ctk.CTkLabel(
                        para_frame,
                        text=text,
                        font=mono_font,
                        text_color=self.TEXT_MUTED,
                        anchor="w",
                        justify="left"
                    ).pack(anchor="w", pady=1)
                elif '<img' in line:
                    match = re.search(r'src="([^"]+)"', line)
                    img_path = match.group(1) if match else "?"
                    ctk.CTkLabel(
                        para_frame,
                        text=f"[Tabulatura: {img_path}]",
                        font=("Roboto", 13),
                        text_color=self.ACCENT_PISTACHIO_DARK,
                        anchor="w"
                    ).pack(anchor="w", pady=5)
                else:
                    text = re.sub(r'<[^>]+>', '', line)
                    if text.strip():
                        if text.startswith('\t'):
                            text = "    " + text.lstrip('\t')
                        ctk.CTkLabel(
                            para_frame,
                            text=text,
                            font=mono_font,
                            anchor="w",
                            justify="left"
                        ).pack(anchor="w", pady=1)

    def _toggle_display_view(self):
        """Toggle between side-by-side and inline chord view."""
        if self.current_mode != "display":
            return
        switch = self.display_widgets.get("view_switch")
        if switch:
            self.display_view_mode = 0 if switch.get() else 1
        self._render_display_text()

    def _format_section_text(self, song: Dict, field: str) -> str:
        """Convert song sections (lyrics/chords) into bracketed text blocks."""
        if not song:
            return ""

        content_order = song.get("content", [])
        section_map = song.get(field, {}) or {}
        lines: List[str] = []

        for section in content_order:
            data = section_map.get(section)
            if data is None:
                fallback_key = section.rstrip('0123456789')
                data = section_map.get(fallback_key)
            if not data:
                continue

            lines.append(f"[{section}]")
            for line in data:
                lines.append(line)
            lines.append("")

        return "\n".join(lines).strip()

    def _get_form_initial_data(self) -> Dict[str, str]:
        """Collect initial values for the form based on current song selection."""
        data = {
            "title": "",
            "artist": "",
            "group": "",
            "language": "",
            "tags": "",
            "key": "",
            "capo": "",
            "bpm": "",
            "timeSignature": "",
            "lyrics": "",
            "chords": "",
        }

        if not self.current_form_song_id:
            return data

        song = get_song(self.current_form_song_id)
        if not song:
            return data

        data.update({
            "title": song.get("title", ""),
            "artist": song.get("artist", ""),
            "group": song.get("group", ""),
            "language": song.get("language", ""),
            "tags": ";".join(song.get("tags", [])),
            "key": song.get("key", ""),
            "capo": str(song.get("capo", "")),
            "bpm": str(song.get("bpm", "")),
            "timeSignature": song.get("timeSignature", ""),
        })

        data["lyrics"] = get_display_lyrics(self.current_form_song_id, 0)
        data["chords"] = get_display_chords(self.current_form_song_id, 0)

        return data

    def _save_form_data(self):
        """Persist data from the inline form."""
        if "title" not in self.form_widgets:
            return

        title = self.form_widgets["title"].get().strip()
        if not title:
            self._show_form_error("Tytuł jest wymagany.")
            return

        metadata = {
            "artist": self.form_widgets.get("artist").get().strip() if self.form_widgets.get("artist") else "",
            "group": self.form_widgets.get("group").get().strip() if self.form_widgets.get("group") else "",
            "language": self.form_widgets.get("language").get().strip() if self.form_widgets.get("language") else "",
            "tags": self.form_widgets.get("tags").get().strip() if self.form_widgets.get("tags") else "",
            "key": self.form_widgets.get("key").get().strip() if self.form_widgets.get("key") else "",
            "capo": self.form_widgets.get("capo").get().strip() if self.form_widgets.get("capo") else "",
            "bpm": self.form_widgets.get("bpm").get().strip() if self.form_widgets.get("bpm") else "",
            "timeSignature": self.form_widgets.get("timeSignature").get().strip() if self.form_widgets.get("timeSignature") else "",
        }

        is_edit = self.current_form_song_id is not None

        try:
            if is_edit:
                if "lyrics" not in self.form_widgets or "chords" not in self.form_widgets:
                    self._show_form_error("Brakuje pól tekstowych.")
                    return

                lyrics_text = self.form_widgets["lyrics"].get("1.0", "end-1c").strip()
                chords_text = self.form_widgets["chords"].get("1.0", "end-1c").strip()

                song_data = {
                    "title": title,
                    "lyrics": lyrics_text,
                    "chords": chords_text,
                    **metadata,
                }

                song_edit(self.current_form_song_id, song_data)
            else:
                combined_box = self.form_widgets.get("combined_content")
                combined_text = combined_box.get("1.0", "end-1c").strip() if combined_box else ""
                if not combined_text:
                    self._show_form_error("Wklej treść piosenki z akordami.")
                    return

                song_id = get_new_song()
                song_data = {
                    "title": title,
                    "lyrics": combined_text,
                    **metadata,
                }
                song_create(song_id, song_data)

        except Exception as exc:
            self._show_form_error(f"Nie udało się zapisać: {exc}")
            return

        # Navigate to song display view
        saved_song_id = self.current_form_song_id if is_edit else song_id
        self.current_form_song_id = None
        self._load_songs()
        self._apply_filters(force=True)
        self._update_tag_checkboxes()
        self._view_song(saved_song_id)

    def _handle_form_cancel(self):
        """Return to the list without saving."""
        self.current_form_song_id = None
        self.current_display_song_id = None
        self.current_mode = "list"
        self.form_widgets = {}
        self.form_error_label = None
        self._restore_left_panel()
        self._render_right_panel()

    def _show_form_error(self, message: str):
        """Display an inline validation error."""
        if self.form_error_label:
            self.form_error_label.configure(text=message)

    def _view_song(self, song_id: int):
        """Show the song preview inline."""
        self.current_display_song_id = song_id
        self.current_mode = "display"
        self.display_view_mode = 0
        self._render_right_panel()

    def _handle_display_back(self):
        """Return from inline display to the list."""
        self.current_form_song_id = None
        self.current_display_song_id = None
        self.current_mode = "list"
        self.display_widgets = {}
        self._restore_left_panel()
        self._render_right_panel()

    def _show_tooltip(self, widget, text: str):
        """Show tooltip popup window on hover."""
        tooltip_window = None
        
        def show(event):
            nonlocal tooltip_window
            if tooltip_window:
                return
            x = widget.winfo_rootx() + 25
            y = widget.winfo_rooty() + 25
            tooltip_window = ctk.CTkToplevel(widget)
            tooltip_window.wm_overrideredirect(True)
            tooltip_window.wm_geometry(f"+{x}+{y}")
            tooltip_window.attributes("-topmost", True)
            
            label = ctk.CTkLabel(
                tooltip_window,
                text=text,
                font=("Roboto", 11),
                fg_color=self.CARD_BG,
                corner_radius=8,
                padx=12,
                pady=8,
                wraplength=300
            )
            label.pack()
        
        def hide(event):
            nonlocal tooltip_window
            if tooltip_window:
                tooltip_window.destroy()
                tooltip_window = None
        
        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def _populate_left_panel_for_form(self, initial_data: Dict[str, str], is_edit: bool):
        """Show title/metadata entries inside the left panel while editing."""
        if not self.left_frame:
            return

        for widget in self.left_frame.winfo_children():
            widget.destroy()
        
        # Scrollable container
        scroll_container = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=5, pady=10)

        def create_entry(key: str, label_text: str, placeholder: str = "", tooltip: str = ""):
            label_frame = ctk.CTkFrame(scroll_container, fg_color="transparent")
            label_frame.pack(pady=(10, 4), padx=15, fill="x")
            
            ctk.CTkLabel(
                label_frame,
                text=label_text,
                font=("Roboto", 15, "bold"),
                anchor="w"
            ).pack(side="left", anchor="w")
            
            if tooltip:
                tooltip_btn = ctk.CTkLabel(
                    label_frame,
                    text=" ⓘ",
                    font=("Roboto", 14),
                    text_color=self.ACCENT_PISTACHIO_DARK,
                    cursor="hand2"
                )
                tooltip_btn.pack(side="left", padx=(5, 0))
                self._show_tooltip(tooltip_btn, tooltip)

            entry = ctk.CTkEntry(
                scroll_container,
                placeholder_text=placeholder,
                height=40,
                font=("Roboto", 13)
            )
            entry.pack(pady=(0, 6), padx=15, fill="x")
            value = initial_data.get(key)
            if value:
                entry.insert(0, value)
            self.form_widgets[key] = entry
        
        def create_dropdown(key: str, label_text: str, values: list, default: str = ""):
            ctk.CTkLabel(
                scroll_container,
                text=label_text,
                font=("Roboto", 15, "bold"),
                anchor="w"
            ).pack(pady=(10, 4), padx=15, anchor="w")
            
            initial_value = initial_data.get(key, default)
            if not initial_value or initial_value not in values:
                initial_value = values[0]
            
            dropdown = ctk.CTkOptionMenu(
                scroll_container,
                values=values,
                height=40,
                font=("Roboto", 13),
                fg_color=self.ACCENT_PISTACHIO_DARK,
                button_color=self.ACCENT_PISTACHIO_DARK,
                button_hover_color="#7FAD5A"
            )
            dropdown.set(initial_value)
            dropdown.pack(pady=(0, 6), padx=15, fill="x")
            self.form_widgets[key] = dropdown

        create_entry("title", "Tytuł", "Np. Amazing Grace", "Pełny tytuł piosenki. To pole jest wymagane.")

        if not is_edit:
            return

        create_entry("artist", "Wykonawca", "np. Anna Jantar", "Nazwa artysty lub zespołu wykonującego piosenkę. Pozostaw puste jeśli nieznany.")
        create_entry("group", "Grupa / Album", "np. Uwielbienie", "Nazwa grupy muzycznej, albumu lub źródła piosenki. Pomocne przy kategoryzowaniu.")
        create_dropdown("language", "Język", ["pl", "eng", "inny"], "pl")
        create_entry("tags", "Tagi", "np. uwielbienie;adwent", "Słowa kluczowe do filtrowania piosenek. Oddziel tagi średnikiem (;). Przykład: adwent;uwielbienie;radość")
        create_entry("key", "Tonacja", "np. C", "Tonacja oryginalna piosenki (np. C, Am, G, D#). Użyj # dla krzyżyków i m dla molowych.")
        create_entry("capo", "Capo", "np. 2", "Numer progu capodastra (0-12). Pozostaw puste lub wpisz 0 jeśli nie używany.")
        create_entry("bpm", "Tempo BPM", "np. 90", "Tempo w uderzeniach na minutę. Typowe wartości: wolne (60-80), średnie (90-120), szybkie (130+).")
        create_entry("timeSignature", "Metrum", "np. 4/4", "Metrum muzyczne, np. 4/4 (najpopularniejsze), 3/4 (walc), 6/8 (marsz). Format: licznik/mianownik.")

    def _restore_left_panel(self):
        """Restore search and filter controls to left panel."""
        if not self.left_frame:
            return
        self._render_filter_controls()

    def _exit_application(self):
        """Close the entire application from the songbook screen."""
        toplevel = self.winfo_toplevel()
        if toplevel:
            toplevel.destroy()

    def _on_back(self):
        """Handle back button click."""
        if self.back_callback:
            self.back_callback()

    def _get_card_bg(self):
        """Get card background color based on theme."""
        key = f"card_bg_{ctk.get_appearance_mode()}"
        if key not in self._color_cache:
            self._color_cache[key] = self.CARD_BG if ctk.get_appearance_mode() == "Light" else self.CARD_BG_DARK
        return self._color_cache[key]

    def _get_card_hover_bg(self):
        """Slightly lighter surface for hover states."""
        key = f"card_hover_{ctk.get_appearance_mode()}"
        if key not in self._color_cache:
            self._color_cache[key] = "#F5F5F5" if ctk.get_appearance_mode() == "Light" else "#1e1e1e"
        return self._color_cache[key]

    def _get_chord_bg(self):
        """Background color for chord labels in preview."""
        key = f"chord_bg_{ctk.get_appearance_mode()}"
        if key not in self._color_cache:
            self._color_cache[key] = "#e8f8f8" if ctk.get_appearance_mode() == "Light" else "#1a3a3a"
        return self._color_cache[key]

    def _get_darker_color(self, hex_color: str) -> str:
        """Return a darker shade of the color."""
        if not hex_color:
            return hex_color

        if not hex_color.startswith('#'):
            # Likely a named color, return original to avoid conversion errors
            return hex_color

        hex_color = hex_color.lstrip('#')

        if len(hex_color) == 3:
            hex_color = ''.join(ch * 2 for ch in hex_color)

        if len(hex_color) != 6:
            return f"#{hex_color}" if hex_color else hex_color

        rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        new_rgb = tuple(int(r * 0.85) for r in rgb)
        return '#%02x%02x%02x' % new_rgb
