import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, modules, show_module_callback, show_menu_callback, header_height=72):
        super().__init__(master, fg_color="white", width=250)
        self.modules = modules
        self.show_module_callback = show_module_callback
        self.show_menu_callback = show_menu_callback
        self.header_height = header_height

        # ustawiamy poza ekranem na start
        self.place(x=-250, y=self.header_height, relheight=1)

        for name, data in self.modules.items():
            btn = ctk.CTkButton(
                self,
                text=f"{data.get('Emoji', '')} {name}",
                fg_color="white",
                text_color="black",
                corner_radius=0,
                border_width=2,
                border_color="white",
                command=lambda k=name: self._sidebar_action(k)
            )
            btn.pack(fill="x", padx=10, pady=5)

            # efekt hover: obramowanie
            btn.bind("<Enter>", lambda e, b=btn, c=data["Color"]: b.configure(border_color=c))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(border_color="white"))

    def toggle(self):
        if self.winfo_x() >= 0:
            self.place(x=-250, y=self.header_height, relheight=1)
        else:
            self.place(x=0, y=self.header_height, relheight=1)

    def _sidebar_action(self, module_name: str):
        if module_name == "Menu":
            self.show_menu_callback()
        else:
            self.show_module_callback(module_name)
        self.toggle()
