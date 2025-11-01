import customtkinter as ctk
import json
import os
import sys
from datetime import datetime, timedelta
import calendar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class CalendarView(ctk.CTkFrame):
    # Visual settings
    PRACTICE_GOAL = 30  # minutes per day
    WEEKLY_GOAL = 180  # 3 hours per week in minutes
    
    COLOR_GOAL_NOT_MET = "#34495E"
    COLOR_GOAL_MET = "#27AE60"
    COLOR_TODAY = "#3498DB"
    COLOR_HEADER = "#1ABC9C"
    COLOR_ACCENT = "#E67E22"
    COLOR_FOCUS = "#F39C12"
    
    def __init__(self, master, show_day_callback=None, back_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Initialize data
        self.practice_data = self._load_practice_data()
        self.current_date = datetime.now()
        self.current_year = self.current_date.year
        self.current_month = self.current_date.month
        
        # Cache for week totals to avoid recalculation
        self.week_totals_cache = {}
        
        # Track focused day - set to today by default
        self.focused_day = self.current_date
        self.focused_day_frame = None
        
        # Callbacks
        self.show_day_callback = show_day_callback
        self.back_callback = back_callback
        
        self._create_widgets()
        
    def _get_data_file_path(self):
        """Get the path to the practice data file (persistent location for exe)."""
        if getattr(sys, 'frozen', False):
            # Running as exe - use AppData folder
            appdata = os.getenv('APPDATA')
            data_dir = os.path.join(appdata, 'Metri')
        else:
            # Running as script - use project directory
            current_file = os.path.abspath(__file__)
            base_dir = os.path.dirname(os.path.dirname(current_file))
            data_dir = os.path.join(base_dir, 'data')
        
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'practice_data.json')
        
    def _load_practice_data(self):
        """Load practice data from JSON file."""
        try:
            data_file = self._get_data_file_path()
            
            print(f"Looking for data file at: {data_file}")
            
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Loaded {len(data)} practice records")
                    return data
            else:
                print(f"Data file not found at {data_file}")
                return {}
        except Exception as e:
            print(f"Error loading practice data: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _save_practice_data(self):
        """Save practice data to JSON file."""
        try:
            data_file = self._get_data_file_path()
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.practice_data, f, indent=2)
        except Exception as e:
            print(f"Error saving practice data: {e}")
    
    def _get_practice_minutes(self, date_obj):
        """Get practice minutes for a specific date."""
        date_str = date_obj.strftime("%Y-%m-%d")
        return self.practice_data.get(date_str, 0)
    
    def _get_week_total(self, date_obj):
        """Calculate total practice time for the week containing the given date."""
        # Find Monday of the week
        days_since_monday = date_obj.weekday()
        monday = date_obj - timedelta(days=days_since_monday)
        week_key = monday.strftime("%Y-%m-%d")
        
        # Use cache if available
        if week_key in self.week_totals_cache:
            return self.week_totals_cache[week_key]
        
        total = 0
        for i in range(7):
            day = monday + timedelta(days=i)
            total += self._get_practice_minutes(day)
        
        self.week_totals_cache[week_key] = total
        return total
    
    def _calculate_daily_streak(self):
        """Calculate current daily streak (consecutive days with practice goal met)."""
        streak = 0
        current = self.current_date
        
        # Go backwards from today
        while True:
            minutes = self._get_practice_minutes(current)
            if minutes >= self.PRACTICE_GOAL:
                streak += 1
                current -= timedelta(days=1)
            else:
                break
            
            # Safety limit
            if streak > 365:
                break
        
        return streak
    
    def _calculate_weekly_streak(self):
        """Calculate current weekly streak (consecutive weeks with weekly goal met)."""
        streak = 0
        current = self.current_date
        
        # Find Monday of current week
        days_since_monday = current.weekday()
        monday = current - timedelta(days=days_since_monday)
        
        # Go backwards week by week
        while True:
            week_total = self._get_week_total(monday)
            if week_total >= self.WEEKLY_GOAL:
                streak += 1
                monday -= timedelta(days=7)
            else:
                break
            
            # Safety limit
            if streak > 52:
                break
        
        return streak
    
    def _get_current_week_progress(self):
        """Get progress percentage for the current week."""
        week_total = self._get_week_total(self.current_date)
        percentage = int((week_total / self.WEEKLY_GOAL) * 100)
        return min(percentage, 100), week_total
    
    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Scrollable frame
        scrollable = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scrollable.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollable.columnconfigure(0, weight=1)
        
        # Header with back button and title in same row
        header_frame = ctk.CTkFrame(scrollable, fg_color="transparent", height=60)
        header_frame.grid(row=0, column=0, pady=(10, 10), sticky="ew", padx=40)
        header_frame.grid_propagate(False)
        header_frame.columnconfigure(1, weight=1)
        
        # Back button on the left
        if self.back_callback:
            back_button = ctk.CTkButton(
                header_frame,
                text="← Powrót",
                command=self.back_callback,
                width=100,
                height=40,
                fg_color="#555555",
                hover_color="#777777",
                font=("Arial", 14)
            )
            back_button.grid(row=0, column=0, padx=(0, 20), sticky="w")
        
        # Title in the center-left
        ctk.CTkLabel(
            header_frame,
            text="Kalendarz Ćwiczeń",
            font=("Arial", 36, "bold"),
            text_color=self.COLOR_HEADER
        ).grid(row=0, column=1, sticky="w")
        
        # Go to day view button on the right
        if self.show_day_callback:
            self.go_to_day_header_button = ctk.CTkButton(
                header_frame,
                text="Dzisiejsze ćwiczenia→",
                command=self._go_to_selected_day,
                width=150,
                height=40,
                font=("Arial", 14, "bold"),
                fg_color=self.COLOR_HEADER,
                hover_color="#16A085",
                corner_radius=10
            )
            self.go_to_day_header_button.grid(row=0, column=2, padx=(20, 0), sticky="e")
        
        # Stats frame (streaks and weekly progress) - align with header
        stats_frame = ctk.CTkFrame(scrollable, fg_color="#2c2c2c", corner_radius=15)
        stats_frame.grid(row=1, column=0, pady=(0, 20), padx=40, sticky="ew")
        
        # Title with decorative line
        title_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        title_container.pack(fill="x", pady=(25, 20))
        title_container.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            title_container,
            text="━━━",
            font=ctk.CTkFont(size=14),
            text_color=self.COLOR_ACCENT
        ).grid(row=0, column=0, padx=(40, 10))
        
        ctk.CTkLabel(
            title_container,
            text="STATYSTYKI",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ECF0F1"
        ).grid(row=0, column=1, sticky="w")
        
        ctk.CTkLabel(
            title_container,
            text="━━━",
            font=ctk.CTkFont(size=14),
            text_color=self.COLOR_ACCENT
        ).grid(row=0, column=2, padx=(10, 40))
        
        # Calculate stats
        daily_streak = self._calculate_daily_streak()
        weekly_streak = self._calculate_weekly_streak()
        week_progress, week_total = self._get_current_week_progress()
        
        # Streak cards container
        streaks_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        streaks_container.pack(fill="x", padx=20, pady=(0, 15))
        streaks_container.columnconfigure(0, weight=1)
        streaks_container.columnconfigure(1, weight=1)
        streaks_container.columnconfigure(0, weight=1)
        streaks_container.columnconfigure(1, weight=1)
        
        # Daily streak card
        daily_streak_frame = ctk.CTkFrame(streaks_container, fg_color="#1e1e1e", corner_radius=12)
        daily_streak_frame.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        ctk.CTkLabel(
            daily_streak_frame,
            text="🔥",
            font=ctk.CTkFont(size=28)
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            daily_streak_frame,
            text="PASSA DZIENNA",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#95a5a6"
        ).pack(pady=(0, 5))
        
        self.daily_streak_label = ctk.CTkLabel(
            daily_streak_frame,
            text=f"{daily_streak}",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.COLOR_ACCENT
        )
        self.daily_streak_label.pack(pady=(0, 5))
        
        ctk.CTkLabel(
            daily_streak_frame,
            text="dni",
            font=ctk.CTkFont(size=12),
            text_color="#7f8c8d"
        ).pack(pady=(0, 20))
        
        # Weekly streak card
        weekly_streak_frame = ctk.CTkFrame(streaks_container, fg_color="#1e1e1e", corner_radius=12)
        weekly_streak_frame.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        
        ctk.CTkLabel(
            weekly_streak_frame,
            text="📅",
            font=ctk.CTkFont(size=28)
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            weekly_streak_frame,
            text="PASSA TYGODNIOWA",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#95a5a6"
        ).pack(pady=(0, 5))
        
        self.weekly_streak_label = ctk.CTkLabel(
            weekly_streak_frame,
            text=f"{weekly_streak}",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.COLOR_TODAY
        )
        self.weekly_streak_label.pack(pady=(0, 5))
        
        ctk.CTkLabel(
            weekly_streak_frame,
            text="tyg.",
            font=ctk.CTkFont(size=12),
            text_color="#7f8c8d"
        ).pack(pady=(0, 20))
        
        # Weekly progress section
        progress_section = ctk.CTkFrame(stats_frame, fg_color="#1e1e1e", corner_radius=12)
        progress_section.pack(fill="x", padx=20, pady=(0, 25))
        
        ctk.CTkLabel(
            progress_section,
            text="POSTĘP TYGODNIOWY",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#95a5a6"
        ).pack(pady=(20, 15))
        
        # Progress bar with custom styling
        progress_container = ctk.CTkFrame(progress_section, fg_color="transparent")
        progress_container.pack(fill="x", padx=30, pady=(0, 10))
        
        progress_color = self.COLOR_GOAL_MET if week_progress >= 100 else self.COLOR_ACCENT
        
        self.week_progress_bar = ctk.CTkProgressBar(
            progress_container,
            height=25,
            progress_color=progress_color,
            corner_radius=12
        )
        self.week_progress_bar.pack(fill="x")
        self.week_progress_bar.set(week_progress / 100)
        
        # Progress text
        self.week_progress_label = ctk.CTkLabel(
            progress_section,
            text=f"{week_total}/{self.WEEKLY_GOAL} min ({week_progress}%)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ECF0F1"
        )
        self.week_progress_label.pack(pady=(10, 20))
        
        # Calendar section with decorative header
        calendar_container = ctk.CTkFrame(scrollable, fg_color="#2c2c2c", corner_radius=15)
        calendar_container.grid(row=2, column=0, pady=(0, 20), padx=40, sticky="ew")
        
        # Month navigation with decorative line
        nav_container = ctk.CTkFrame(calendar_container, fg_color="transparent")
        nav_container.pack(fill="x", pady=(25, 15))
        nav_container.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            nav_container,
            text="━━━",
            font=ctk.CTkFont(size=14),
            text_color=self.COLOR_TODAY
        ).grid(row=0, column=0, padx=(40, 10))
        
        nav_frame = ctk.CTkFrame(nav_container, fg_color="transparent")
        nav_frame.grid(row=0, column=1)
        
        prev_button = ctk.CTkButton(
            nav_frame,
            text="◄",
            command=self._previous_month,
            width=45,
            height=40,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color=self.COLOR_TODAY,
            hover_color="#2980B9",
            corner_radius=10
        )
        prev_button.pack(side="left", padx=10)
        
        self.month_label = ctk.CTkLabel(
            nav_frame,
            text="",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ECF0F1",
            width=300
        )
        self.month_label.pack(side="left", padx=20)
        
        next_button = ctk.CTkButton(
            nav_frame,
            text="►",
            command=self._next_month,
            width=45,
            height=40,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color=self.COLOR_TODAY,
            hover_color="#2980B9",
            corner_radius=10
        )
        next_button.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            nav_container,
            text="━━━",
            font=ctk.CTkFont(size=14),
            text_color=self.COLOR_TODAY
        ).grid(row=0, column=2, padx=(10, 40))
        
        # Calendar frame
        self.calendar_frame = ctk.CTkFrame(calendar_container, fg_color="transparent")
        self.calendar_frame.pack(pady=(15, 25), padx=20)
        
        # Chart frame - moved inside calendar container
        self.chart_frame = ctk.CTkFrame(scrollable, fg_color="#2c2c2c", corner_radius=15)
        self.chart_frame.grid(row=3, column=0, pady=(0, 20), padx=40, sticky="ew")
        
        # Day details panel (initially hidden)
        self.details_panel = ctk.CTkFrame(scrollable, fg_color="#2c2c2c", corner_radius=15)
        self.details_panel.grid(row=4, column=0, pady=(0, 20), padx=40, sticky="ew")
        self.details_panel.grid_remove()  # Hide initially
        
        # Title with decorative line for details
        details_title_container = ctk.CTkFrame(self.details_panel, fg_color="transparent")
        details_title_container.pack(fill="x", pady=(25, 15))
        details_title_container.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            details_title_container,
            text="━━━",
            font=ctk.CTkFont(size=14),
            text_color=self.COLOR_FOCUS
        ).grid(row=0, column=0, padx=(40, 10))
        
        ctk.CTkLabel(
            details_title_container,
            text="SZCZEGÓŁY DNIA",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ECF0F1"
        ).grid(row=0, column=1, sticky="w")
        
        ctk.CTkLabel(
            details_title_container,
            text="━━━",
            font=ctk.CTkFont(size=14),
            text_color=self.COLOR_FOCUS
        ).grid(row=0, column=2, padx=(10, 40))
        
        details_content_frame = ctk.CTkFrame(self.details_panel, fg_color="transparent")
        details_content_frame.pack(fill="both", expand=True, padx=40, pady=(0, 25))
        details_content_frame.columnconfigure(0, weight=1)
        
        # Day details info
        self.details_label = ctk.CTkLabel(
            details_content_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#ECF0F1",
            justify="left"
        )
        self.details_label.grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        # Edit practice time section
        edit_frame = ctk.CTkFrame(details_content_frame, fg_color="#1e1e1e", corner_radius=12)
        edit_frame.grid(row=1, column=0, sticky="ew", pady=(0, 0))
        
        edit_inner = ctk.CTkFrame(edit_frame, fg_color="transparent")
        edit_inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            edit_inner,
            text="Zmień czas ćwiczeń:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#95a5a6"
        ).pack(anchor="w", pady=(0, 10))
        
        time_input_frame = ctk.CTkFrame(edit_inner, fg_color="transparent")
        time_input_frame.pack(anchor="w")
        
        self.minutes_entry = ctk.CTkEntry(
            time_input_frame,
            width=100,
            height=40,
            font=ctk.CTkFont(size=16),
            placeholder_text="0"
        )
        self.minutes_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            time_input_frame,
            text="minut",
            font=ctk.CTkFont(size=14),
            text_color="#ECF0F1"
        ).pack(side="left", padx=(0, 15))
        
        self.save_time_button = ctk.CTkButton(
            time_input_frame,
            text="Zapisz",
            command=self._save_practice_time,
            width=80,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.COLOR_GOAL_MET,
            hover_color="#229954",
            corner_radius=20
        )
        self.save_time_button.pack(side="left")
        
        # Initial render
        self._render_calendar()
        self._render_chart()
        
        # Show today's details automatically after a brief delay
        self.after(100, self._select_today)
    
    def _render_calendar(self):
        """Render the calendar for the current month."""
        # Clear cache for new month
        self.week_totals_cache.clear()
        
        # Clear existing calendar
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        # Reset focused frame reference since widgets are destroyed
        self.focused_day_frame = None
        
        # Update month label
        month_names = [
            "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
            "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"
        ]
        self.month_label.configure(
            text=f"{month_names[self.current_month - 1]} {self.current_year}"
        )
        
        # Create calendar grid
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        
        # Day headers
        day_names = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nie"]
        for col, day_name in enumerate(day_names):
            header = ctk.CTkLabel(
                self.calendar_frame,
                text=day_name,
                font=("Arial", 16, "bold"),
                width=85,
                height=35,
                fg_color="#1e1e1e",
                corner_radius=8
            )
            header.grid(row=0, column=col, padx=3, pady=3)
        
        # Debug: Print what we're looking for
        print(f"\n=== Rendering calendar for {self.current_year}-{self.current_month:02d} ===")
        
        # Calendar days - optimized rendering
        week_goals_to_show = {}  # Store week totals for indicators
        
        for week_num, week in enumerate(cal, start=1):
            week_total = 0
            week_start_date = None
            
            for day_num, day in enumerate(week):
                if day == 0:
                    # Empty cell - lighter weight
                    continue
                else:
                    # Create date object
                    date_obj = datetime(self.current_year, self.current_month, day)
                    minutes = self._get_practice_minutes(date_obj)
                    
                    # Track week start for calculating total
                    if week_start_date is None:
                        week_start_date = date_obj
                    
                    # Debug: Print some sample days
                    if day <= 5:
                        date_str = date_obj.strftime("%Y-%m-%d")
                        print(f"Day {day}: {date_str} = {minutes} minutes (Goal: {self.PRACTICE_GOAL})")
                    
                    # Determine color - simplified logic
                    is_today = (
                        date_obj.year == self.current_date.year and
                        date_obj.month == self.current_date.month and
                        date_obj.day == self.current_date.day
                    )
                    
                    # Check if this is the focused day
                    is_focused = (
                        self.focused_day is not None and
                        date_obj.year == self.focused_day.year and
                        date_obj.month == self.focused_day.month and
                        date_obj.day == self.focused_day.day
                    )
                    
                    if is_today:
                        bg_color = self.COLOR_TODAY
                        border_width = 3
                        border_color = "white"
                    elif minutes >= self.PRACTICE_GOAL:
                        bg_color = self.COLOR_GOAL_MET
                        border_width = 3 if is_focused else 0
                        border_color = "#F39C12"
                    else:
                        bg_color = self.COLOR_GOAL_NOT_MET
                        border_width = 3 if is_focused else 0
                        border_color = "#F39C12"
                    
                    # Create day cell - CIRCULAR (corner_radius = half of size for perfect circle)
                    day_frame = ctk.CTkFrame(
                        self.calendar_frame,
                        fg_color=bg_color,
                        width=85,
                        height=85,
                        corner_radius=43,  # Nearly half of 85 for circular look
                        border_width=border_width,
                        border_color=border_color if is_focused else ("white" if is_today else "")
                    )
                    day_frame.grid(row=week_num, column=day_num, padx=3, pady=3)
                    day_frame.grid_propagate(False)
                    
                    # If this is the focused day, update the reference
                    if is_focused:
                        self.focused_day_frame = day_frame
                    
                    # Day number
                    day_label = ctk.CTkLabel(
                        day_frame,
                        text=str(day),
                        font=("Arial", 22, "bold"),
                        text_color="white"
                    )
                    day_label.place(relx=0.5, rely=0.5, anchor="center")
                    
                    # Make clickable
                    day_frame.bind("<Button-1>", lambda e, d=date_obj, f=day_frame: self._on_day_click(d, f))
                    day_label.bind("<Button-1>", lambda e, d=date_obj, f=day_frame: self._on_day_click(d, f))
            
            # Calculate week total and add indicator
            if week_start_date is not None:
                week_total = self._get_week_total(week_start_date)
                week_goals_to_show[week_num] = week_total
        
        # Add weekly goal indicators
        for week_num, week_total in week_goals_to_show.items():
            goal_met = week_total >= self.WEEKLY_GOAL
            percentage = int((week_total / self.WEEKLY_GOAL) * 100)
            
            # Create indicator frame
            indicator_frame = ctk.CTkFrame(
                self.calendar_frame,
                fg_color="transparent",
                width=60,
                height=85
            )
            indicator_frame.grid(row=week_num, column=7, padx=(10, 0), pady=3)
            indicator_frame.grid_propagate(False)
            
            # Add checkmark or X
            if goal_met:
                symbol = "✓"
                symbol_color = self.COLOR_GOAL_MET
            else:
                symbol = "✗"
                symbol_color = "#E74C3C"
            
            symbol_label = ctk.CTkLabel(
                indicator_frame,
                text=symbol,
                font=("Arial", 28, "bold"),
                text_color=symbol_color
            )
            symbol_label.place(relx=0.5, rely=0.35, anchor="center")
            
            # Percentage instead of time
            percentage_label = ctk.CTkLabel(
                indicator_frame,
                text=f"{percentage}%",
                font=("Arial", 13, "bold"),
                text_color="white" if goal_met else "#E74C3C"
            )
            percentage_label.place(relx=0.5, rely=0.72, anchor="center")
    
    def _render_chart(self):
        """Render the monthly practice time chart."""
        # Clear existing chart properly
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Force update to clear any artifacts
        self.chart_frame.update_idletasks()
        
        # Get data for current month
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        days = []
        minutes_list = []
        
        for week in cal:
            for day in week:
                if day != 0:
                    date_obj = datetime(self.current_year, self.current_month, day)
                    days.append(day)
                    minutes_list.append(self._get_practice_minutes(date_obj))
        
        # Create matplotlib figure with optimized settings
        fig = Figure(figsize=(10, 3.5), facecolor='none', dpi=80)  # 'none' = transparent
        ax = fig.add_subplot(111)
        
        # Plot data
        bars = ax.bar(days, minutes_list, color='#34495E', edgecolor='none', width=0.8)
        
        # Color bars based on goal
        for i, minutes in enumerate(minutes_list):
            if minutes >= self.PRACTICE_GOAL:
                bars[i].set_color('#27AE60')
        
        # Add goal line
        ax.axhline(y=self.PRACTICE_GOAL, color='#F39C12', linestyle='--', 
                   linewidth=2, label=f'Cel ({self.PRACTICE_GOAL} min)', alpha=0.8)
        
        # Styling
        ax.set_xlabel('Dzień', color='white', fontsize=11, fontweight='bold')
        ax.set_ylabel('Minuty', color='white', fontsize=11, fontweight='bold')
        ax.set_title(f'Przegląd miesiąca', color='white', fontsize=14, fontweight='bold', pad=15)
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white', labelsize=9)
        ax.spines['bottom'].set_color('#555')
        ax.spines['left'].set_color('#555')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.legend(facecolor='#2B2B2B', edgecolor='#555', labelcolor='white', 
                 fontsize=10, loc='upper right')
        ax.grid(True, alpha=0.15, color='white', linestyle='-', linewidth=0.5)
        
        # Optimize layout
        fig.tight_layout(pad=1.5)
        
        # Embed in tkinter with transparent background
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg='#2B2B2B', highlightthickness=0)  # Match app background
        widget.pack(fill="both", expand=True, padx=20, pady=10)
    
    def _previous_month(self):
        """Navigate to previous month."""
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        
        # Clear focus when changing months
        self.focused_day = None
        self.focused_day_frame = None
        self.details_panel.grid_remove()
        
        self._render_calendar()
        self._render_chart()
    
    def _next_month(self):
        """Navigate to next month."""
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        
        # Clear focus when changing months
        self.focused_day = None
        self.focused_day_frame = None
        self.details_panel.grid_remove()
        
        self._render_calendar()
        self._render_chart()
    
    def _on_day_click(self, date_obj, day_frame):
        """Handle day cell click to focus on a specific day."""
        # Remove previous focus border
        if self.focused_day_frame is not None and self.focused_day_frame.winfo_exists():
            # Reset border - check if it's today
            is_prev_today = (
                self.focused_day is not None and
                self.focused_day.year == self.current_date.year and
                self.focused_day.month == self.current_date.month and
                self.focused_day.day == self.current_date.day
            )
            if is_prev_today:
                self.focused_day_frame.configure(border_width=3, border_color="white")
            else:
                self.focused_day_frame.configure(border_width=0)
        
        # Add focus border to clicked day
        self.focused_day = date_obj
        self.focused_day_frame = day_frame
        day_frame.configure(border_width=3, border_color="#F39C12")  # Orange focus border
        
        # Show details panel
        self._show_day_details(date_obj)
    
    def _show_day_details(self, date_obj):
        """Display detailed information about the selected day."""
        minutes = self._get_practice_minutes(date_obj)
        week_total = self._get_week_total(date_obj)
        
        # Format date
        date_str = date_obj.strftime("%d %B %Y")
        day_names_polish = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        day_name = day_names_polish[date_obj.weekday()]
        
        # Format practice time
        if minutes > 0:
            hours = minutes // 60
            mins = minutes % 60
            if hours > 0:
                time_text = f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
            else:
                time_text = f"{mins}m"
        else:
            time_text = "Brak ćwiczeń"
        
        # Goal status
        if minutes >= self.PRACTICE_GOAL:
            goal_status = "✓ Cel dzienny osiągnięty"
            goal_color = self.COLOR_GOAL_MET
        else:
            remaining = self.PRACTICE_GOAL - minutes
            goal_status = f"✗ Do celu brakuje: {remaining} min"
            goal_color = "#E74C3C"
        
        # Week info
        week_hours = week_total // 60
        week_mins = week_total % 60
        week_time_text = f"{week_hours}h {week_mins}m" if week_mins > 0 else f"{week_hours}h"
        week_percentage = int((week_total / self.WEEKLY_GOAL) * 100)
        
        if week_total >= self.WEEKLY_GOAL:
            week_status = f"✓ Cel tygodniowy osiągnięty ({week_percentage}%)"
        else:
            week_status = f"Postęp tygodniowy: {week_percentage}%"
        
        # Update details text
        details_text = f"""📅 {day_name}, {date_str}
        
⏱️  Czas ćwiczeń: {time_text}
{goal_status}

📊 Tydzień: {week_time_text} ({week_status})"""
        
        self.details_label.configure(text=details_text)
        
        # Populate the entry with current minutes
        self.minutes_entry.delete(0, 'end')
        self.minutes_entry.insert(0, str(minutes))
        
        self.details_panel.grid()  # Show panel
    
    def _save_practice_time(self):
        """Save the manually entered practice time for the selected day."""
        if not self.focused_day:
            return
        
        try:
            minutes = int(self.minutes_entry.get())
            if minutes < 0:
                minutes = 0
            if minutes > 1440:  # Max 24 hours
                minutes = 1440
            
            # Update data
            date_str = self.focused_day.strftime("%Y-%m-%d")
            self.practice_data[date_str] = minutes
            self._save_practice_data()
            
            # Clear cache and refresh
            self.week_totals_cache.clear()
            
            # Store the focused day before re-rendering
            focused_date = self.focused_day
            
            # Re-render calendar and chart
            self._render_calendar()
            self._render_chart()
            
            # Update stats (streaks and progress)
            self._update_stats()
            
            # Re-select the same day
            for widget in self.calendar_frame.winfo_children():
                if isinstance(widget, ctk.CTkFrame) and widget.winfo_exists():
                    # Find the frame that matches our date
                    # We'll trigger a click event after render completes
                    pass
            
            # Update details panel
            self._show_day_details(focused_date)
            
        except ValueError:
            # Invalid input, ignore
            pass
    
    def _update_stats(self):
        """Update the streak counters and weekly progress bar."""
        # Recalculate stats
        daily_streak = self._calculate_daily_streak()
        weekly_streak = self._calculate_weekly_streak()
        week_progress, week_total = self._get_current_week_progress()
        
        # Update labels with new format (just numbers)
        self.daily_streak_label.configure(text=f"{daily_streak}")
        self.weekly_streak_label.configure(text=f"{weekly_streak}")
        self.week_progress_label.configure(
            text=f"{week_total}/{self.WEEKLY_GOAL} min ({week_progress}%)"
        )
        
        # Update progress bar
        progress_color = self.COLOR_GOAL_MET if week_progress >= 100 else self.COLOR_ACCENT
        self.week_progress_bar.configure(progress_color=progress_color)
        self.week_progress_bar.set(week_progress / 100)
    
    def _go_to_selected_day(self):
        """Navigate to the day view for today."""
        if self.show_day_callback:
            self.show_day_callback(self.current_date)
    
    def _select_today(self):
        """Automatically select and show details for today."""
        if self.focused_day:
            self._show_day_details(self.focused_day)