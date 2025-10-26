import customtkinter as ctk

class SettingsView(ctk.CTkFrame):
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._create_widgets()
        
    def _create_widgets(self):
        content = ctk.CTkFrame(self)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        title = ctk.CTkLabel(
            content,
            text="USTAWIENIA",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=(20, 10))
        
        description = ctk.CTkLabel(
            content,
            text="Na tym ekranie użytkownik będzie mógł dostosować ustawienia aplikacji.",
            font=("Arial", 14),
            wraplength=400
        )
        description.pack(pady=10)