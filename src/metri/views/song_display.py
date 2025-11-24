import customtkinter as ctk
from typing import Callable, Optional
import os
import sys
import re
from PIL import Image

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ..logic.song_func import get_song
from ..logic.display_func import get_display
from ..logic.keys import transpose


class SongDisplayView(ctk.CTkFrame):
    """Display view for showing a song with lyrics and chords."""

    # Colors matching the app theme
    ACCENT_CYAN = "#25b4b6"
    ACCENT_GOLD = "#cca839"
    ACCENT_PURPLE = "#552564"
    ACCENT_GREEN = "#2ECC71"
    ACCENT_RED = "#E74C3C"
    BG_LIGHT = "#f2f2f2"
    BG_DARK = "#1a1a1a"
    CARD_BG = "#FFFFFF"
    CARD_BG_DARK = "#2b2b2b"

    def __init__(self, master, song_id: int, back_callback: Optional[Callable] = None,
                 edit_callback: Optional[Callable[[int], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.song_id = song_id
        self.back_callback = back_callback
        self.edit_callback = edit_callback
        self.configure(fg_color="transparent")

        # Transposition state
        self.transpose_value = 0

        # Load song data
        self.song = get_song(song_id)
        
        if not self.song:
            self._show_error()
            return

        # Build UI
        self._build_ui()

    def _show_error(self):
        """Show error message if song not found."""
        ctk.CTkLabel(
            self,
            text="⚠️ Piosenka nie znaleziona",
            font=("Roboto", 24, "bold"),
            text_color=self.ACCENT_RED
        ).pack(expand=True)

        ctk.CTkButton(
            self,
            text="← Powrót",
            command=self._on_back,
            width=130,
            height=40,
            fg_color=self.ACCENT_PURPLE,
            hover_color=self._get_darker_color(self.ACCENT_PURPLE),
            font=("Roboto", 14),
            corner_radius=10
        ).pack(pady=20)

    def _build_ui(self):
        """Build the main UI structure."""
        # Header bar
        self._create_header()

        # Main content area
        self._create_content()

    def _create_header(self):
        """Create the header bar with back button, title, and controls."""
        header = ctk.CTkFrame(self, fg_color=self.CARD_BG, height=120, corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.pack_propagate(False)

        # Top row - back button and title
        top_row = ctk.CTkFrame(header, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(15, 5))

        left = ctk.CTkFrame(self.header, fg_color="transparent")
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")

        if os.path.exists(icon_path):
            self.app_icon = ctk.CTkImage(light_image=Image.open(icon_path), size=(60, 65))
            self.menu_button = ctk.CTkButton(
                left,
                image=self.app_icon,
                text="",
                width=60,
                height=65,
                fg_color="transparent",
                command=self.sidebar.toggle  # <<< zawsze ten sam sidebar
            )
            self.menu_button.pack(side="left", anchor="center")
        # Back button
        back_btn = ctk.CTkButton(
            top_row,
            text="← Powrót",
            command=self._on_back,
            width=130,
            height=40,
            fg_color=self.ACCENT_PURPLE,
            hover_color=self._get_darker_color(self.ACCENT_PURPLE),
            font=("Roboto", 14),
            corner_radius=10
        ).pack(side="left", anchor="center", padx=(10, 0))

        # Song info
        info_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        info_frame.pack(side="left", padx=(20, 0), fill="x", expand=True)

        # Title
        title_text = self.song.get("title", "Bez tytułu")
        ctk.CTkLabel(
            info_frame,
            text=title_text,
            font=("Roboto", 28, "bold"),
            text_color=self.ACCENT_CYAN,
            anchor="w"
        ).pack(anchor="w")

        # Artist
        artist_text = self.song.get("artist", "")
        if artist_text:
            ctk.CTkLabel(
                info_frame,
                text=f"🎤 {artist_text}",
                font=("Roboto", 16),
                text_color="gray",
                anchor="w"
            ).pack(anchor="w")

        if self.edit_callback:
            ctk.CTkButton(
                top_row,
                text="✏️ Edytuj",
                command=self._on_edit,
                width=120,
                height=40,
                fg_color=self.ACCENT_GREEN,
                hover_color=self._get_darker_color(self.ACCENT_GREEN),
                font=("Roboto", 14, "bold"),
                corner_radius=10
            ).pack(side="right")

        # Bottom row - transpose controls
        controls_row = ctk.CTkFrame(header, fg_color="transparent")
        controls_row.pack(fill="x", padx=20, pady=(5, 15))

        # Transpose label
        ctk.CTkLabel(
            controls_row,
            text="Transpozycja:",
            font=("Roboto", 14, "bold")
        ).pack(side="left", padx=(0, 10))

        # Transpose down button
        ctk.CTkButton(
            controls_row,
            text="−",
            command=self._transpose_down,
            width=40,
            height=40,
            fg_color=self.ACCENT_GOLD,
            hover_color=self._get_darker_color(self.ACCENT_GOLD),
            font=("Roboto", 20, "bold"),
            corner_radius=10
        ).pack(side="left", padx=2)

        # Transpose value display
        self.transpose_label = ctk.CTkLabel(
            controls_row,
            text=f"{self.transpose_value:+d}",
            font=("Roboto", 16, "bold"),
            width=60
        )
        self.transpose_label.pack(side="left", padx=10)

        # Transpose up button
        ctk.CTkButton(
            controls_row,
            text="+",
            command=self._transpose_up,
            width=40,
            height=40,
            fg_color=self.ACCENT_GOLD,
            hover_color=self._get_darker_color(self.ACCENT_GOLD),
            font=("Roboto", 20, "bold"),
            corner_radius=10
        ).pack(side="left", padx=2)

        # Reset button
        ctk.CTkButton(
            controls_row,
            text="Reset",
            command=self._reset_transpose,
            width=80,
            height=40,
            fg_color=self.ACCENT_CYAN,
            hover_color=self._get_darker_color(self.ACCENT_CYAN),
            font=("Roboto", 14, "bold"),
            corner_radius=10
        ).pack(side="left", padx=(15, 0))

        # Key display
        key = self.song.get('key', '')
        if key:
            key_frame = ctk.CTkFrame(controls_row, fg_color=self.ACCENT_PURPLE, corner_radius=8)
            key_frame.pack(side="right", padx=(10, 0))
            
            ctk.CTkLabel(
                key_frame,
                text=f"Tonacja: {key}",
                font=("Roboto", 14, "bold"),
                text_color="white",
                padx=15,
                pady=8
            ).pack()

    def _create_content(self):
        """Create the main content area with song display."""
        content_frame = ctk.CTkFrame(self, fg_color=self.CARD_BG, corner_radius=12)
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Scrollable text area
        self.text_scroll = ctk.CTkScrollableFrame(
            content_frame,
            fg_color="transparent",
            corner_radius=0
        )
        self.text_scroll.pack(fill="both", expand=True, padx=30, pady=30)

        # Display song
        self._display_song()

    def _display_song(self):
        """Display the song using display_func."""
        # Clear existing content
        for widget in self.text_scroll.winfo_children():
            widget.destroy()

        try:
            # Get formatted display from display_func
            display_text = get_display(self.song_id, self.transpose_value)
            
            # Parse and display the formatted text
            self._parse_and_display(display_text)
            
        except Exception as e:
            print(f"Error displaying song: {e}")
            ctk.CTkLabel(
                self.text_scroll,
                text=f"⚠️ Błąd wyświetlania piosenki: {str(e)}",
                font=("Roboto", 14),
                text_color=self.ACCENT_RED
            ).pack(pady=20)

    def _parse_and_display(self, display_text: str):
        """Parse HTML-like formatted text and display it."""
        # Split by paragraphs
        paragraphs = display_text.split('\n\n')
        
        for para in paragraphs:
            if not para.strip():
                continue
            
            # Create frame for paragraph
            para_frame = ctk.CTkFrame(self.text_scroll, fg_color="transparent")
            para_frame.pack(fill="x", pady=(0, 20))
            
            lines = para.strip().split('\n')
            for line in lines:
                if not line.strip():
                    # Empty line - add spacing
                    ctk.CTkLabel(para_frame, text="", height=5).pack()
                    continue
                
                # Check for bold (chords or section headers)
                if '<b>' in line:
                    # Extract text from <b> tags
                    text = re.sub(r'</?b>', '', line)
                    
                    # Check if it contains <code> tags (chords)
                    if '<code>' in text:
                        # Parse chords
                        chord_frame = ctk.CTkFrame(para_frame, fg_color="transparent")
                        chord_frame.pack(fill="x", pady=(2, 0))
                        
                        # Split by code tags and create labels
                        parts = re.split(r'<code>|</code>', text)
                        current_x = 0
                        
                        for i, part in enumerate(parts):
                            if not part.strip():
                                continue
                            
                            if i % 2 == 1:  # Inside code tag (chord)
                                chord_label = ctk.CTkLabel(
                                    chord_frame,
                                    text=part,
                                    font=("Courier New", 13, "bold"),
                                    text_color=self.ACCENT_CYAN,
                                    fg_color=self._get_chord_bg(),
                                    corner_radius=4,
                                    padx=4,
                                    pady=2
                                )
                                chord_label.pack(side="left", padx=(current_x, 2))
                                current_x = 0
                            else:  # Outside code tag (spacing)
                                # Add spacing based on text length
                                if part:
                                    current_x += len(part) * 3
                    else:
                        # Regular bold text (section intro or emphasis)
                        ctk.CTkLabel(
                            para_frame,
                            text=text,
                            font=("Roboto", 14, "bold"),
                            text_color=self.ACCENT_PURPLE,
                            anchor="w",
                            justify="left"
                        ).pack(anchor="w", pady=(5, 2))
                
                # Check for italic (second voice)
                elif '<i>' in line:
                    text = re.sub(r'</?i>', '', line)
                    ctk.CTkLabel(
                        para_frame,
                        text=text,
                        font=("Roboto", 13, "italic"),
                        text_color="gray",
                        anchor="w",
                        justify="left"
                    ).pack(anchor="w", pady=1)
                
                # Check for image (tab)
                elif '<img' in line:
                    # Extract image path
                    match = re.search(r'src="([^"]+)"', line)
                    if match:
                        img_path = match.group(1)
                        ctk.CTkLabel(
                            para_frame,
                            text=f"[Tabulatura: {img_path}]",
                            font=("Roboto", 12),
                            text_color=self.ACCENT_GOLD,
                            anchor="w"
                        ).pack(anchor="w", pady=5)
                
                # Regular lyrics
                else:
                    # Remove any remaining HTML tags
                    text = re.sub(r'<[^>]+>', '', line)
                    if text.strip():
                        # Check for tab character (chorus)
                        if text.startswith('\t'):
                            text = text.lstrip('\t')
                            text = "    " + text  # Replace tab with spaces
                        
                        ctk.CTkLabel(
                            para_frame,
                            text=text,
                            font=("Roboto", 13),
                            anchor="w",
                            justify="left"
                        ).pack(anchor="w", pady=1)

    def _transpose_up(self):
        """Transpose up by one semitone."""
        self.transpose_value += 1
        if self.transpose_value > 11:
            self.transpose_value = 11
        self._update_transpose()

    def _transpose_down(self):
        """Transpose down by one semitone."""
        self.transpose_value -= 1
        if self.transpose_value < -11:
            self.transpose_value = -11
        self._update_transpose()

    def _reset_transpose(self):
        """Reset transpose to 0."""
        self.transpose_value = 0
        self._update_transpose()

    def _update_transpose(self):
        """Update the display after transposition change."""
        self.transpose_label.configure(text=f"{self.transpose_value:+d}")
        self._display_song()

    def _on_back(self):
        """Handle back button click."""
        if self.back_callback:
            self.back_callback()

    def _on_edit(self):
        """Handle edit button click."""
        if self.edit_callback:
            self.edit_callback(self.song_id)

    def _get_chord_bg(self):
        """Get chord background color based on theme."""
        if ctk.get_appearance_mode() == "Light":
            return "#e8f8f8"
        else:
            return "#1a3a3a"

    def _get_darker_color(self, hex_color: str) -> str:
        """Return a darker shade of the color."""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        new_rgb = tuple(int(r * 0.85) for r in rgb)
        return '#%02x%02x%02x' % new_rgb
