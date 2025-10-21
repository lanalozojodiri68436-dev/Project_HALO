# -*- coding: utf-8 -*-
"""
UI Interface for HALO (with Right-Click Context Menu + Highlight)
=================================================================
"""
import tkinter as tk
from tkinter import scrolledtext
from loguru import logger
import tkinter.simpledialog as simpledialog
import os
from pathlib import Path

class UIDashboard:
    """A powerful Tkinter-based GUI for HALO."""

    def __init__(self):
        """Initializes the UI dashboard window and widgets."""
        logger.info("Initializing UIDashboard...")
        self.root = tk.Tk()
        self.root.title("HALO Control Panel")
        self.root.geometry("800x600")
        
        self.status_label_var = tk.StringVar(value="HALO Status: Idle")
        self.status_label = tk.Label(self.root, textvariable=self.status_label_var, font=("Arial", 12))
        self.status_label.pack(side=tk.TOP, pady=5)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, pady=10)
        self.voice_button = tk.Button(button_frame, text="Voice Command", font=("Arial", 12))
        self.voice_button.pack(side=tk.LEFT, padx=10)
        self.text_button = tk.Button(button_frame, text="Text Command", font=("Arial", 12))
        self.text_button.pack(side=tk.LEFT, padx=10)

        self.log_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', font=("Consolas", 10))
        self.log_display.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        # --- Context Menu ---
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="打开文件", command=self._open_file)
        self.context_menu.add_command(label="打开路径", command=self._open_path)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="复制完整路径", command=self._copy_full_path)
        self.context_menu.add_command(label="复制文件名", command=self._copy_filename)

        self.line_to_path_map = {}
        self.selected_path: Path | None = None
        
        # --- [NEW] Highlight Tag and Event Bindings ---
        # 1. Define the 'highlight' tag style
        self.log_display.tag_configure(
            "highlight", 
            background="#e9e9e9",  # A light gray background
            # foreground="black"  # You can also change text color if you want
        )
        
        # 2. Bind right-click to show menu (existing)
        self.log_display.bind("<Button-3>", self._show_context_menu)
        # 3. Bind left-click to clear the highlight
        self.log_display.bind("<Button-1>", self._clear_highlight)
        
        logger.info("UIDashboard initialized successfully.")

    # --- [NEW] Function to clear highlight on left-click ---
    def _clear_highlight(self, event):
        """Removes highlight tag from the entire text widget."""
        self.log_display.tag_remove("highlight", "1.0", "end")

    # --- [MODIFIED] Context Menu Handler (with highlight logic) ---
    def _show_context_menu(self, event):
        """Shows the context menu on right-click and highlights the line."""
        
        # [MODIFIED] Always remove previous highlight first
        self._clear_highlight(event)
        
        index = self.log_display.index(f"@{event.x},{event.y}")
        line_num = int(index.split('.')[0])
        
        self.selected_path = self.line_to_path_map.get(line_num)
        
        if self.selected_path:
            # [NEW] Add highlight to the selected line
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"
            self.log_display.tag_add("highlight", line_start, line_end)
            
            # (Existing logic to enable menu items)
            for i in range(self.context_menu.index("end") + 1):
                if self.context_menu.type(i) == "command":
                    self.context_menu.entryconfig(i, state="normal")
            
            self.context_menu.tk_popup(event.x_root, event.y_root)
        else:
            self.selected_path = None

    def _open_file(self):
        if self.selected_path and self.selected_path.is_file():
            os.startfile(self.selected_path)

    def _open_path(self):
        if self.selected_path:
            os.startfile(self.selected_path.parent)

    def _copy_full_path(self):
        if self.selected_path:
            self.root.clipboard_clear()
            self.root.clipboard_append(str(self.selected_path))

    def _copy_filename(self):
        if self.selected_path:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.selected_path.name)

    # --- Existing Methods ---
    def add_log(self, message: str):
        self.root.after(0, self._add_log_callback, message, None)

    def add_search_result(self, display_text: str, file_paths: list[Path]):
        self.root.after(0, self._add_log_callback, display_text, file_paths)
    
    def _add_log_callback(self, message: str, file_paths: list[Path] | None):
        self.log_display.config(state='normal')
        start_line = int(self.log_display.index('end-1c').split('.')[0])
        self.log_display.insert(tk.END, message + "\n\n")
        if file_paths:
            for i, path in enumerate(file_paths):
                line_index = start_line + 3 + i
                self.line_to_path_map[line_index] = path
        self.log_display.config(state='disabled')
        self.log_display.see(tk.END)

    def get_text_input(self, title: str, prompt: str) -> str | None:
        return simpledialog.askstring(title, prompt, parent=self.root)

    def update_status(self, new_status: str):
        self.root.after(0, self._update_status_callback, new_status)

    def _update_status_callback(self, new_status: str):
        self.status_label_var.set(f"HALO Status: {new_status}")

    def run(self):
        logger.info("Starting UI main loop.")
        self.root.mainloop()