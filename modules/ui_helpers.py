import tkinter as tk
from tkinter import ttk


def _center_window(window, parent):
    window.update_idletasks()
    if parent is None:
        return
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()
    win_w = window.winfo_width()
    win_h = window.winfo_height()
    x = parent_x + (parent_w - win_w) // 2
    y = parent_y + (parent_h - win_h) // 2
    window.geometry(f"+{x}+{y}")


def _build_dialog(parent, title, message, variant="info", confirm=False):
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.configure(bg="#f5f7fb")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    container = ttk.Frame(dialog)
    container.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

    header = ttk.Label(container, text=title)
    header.pack(anchor="w", pady=(0, 6))

    message_label = ttk.Label(container, text=message, wraplength=360)
    message_label.pack(anchor="w", pady=(0, 12))

    button_frame = ttk.Frame(container)
    button_frame.pack(fill=tk.X)

    result = {"value": False}

    if confirm:
        ttk.Button(button_frame, text="İptal", command=lambda: dialog.destroy()).pack(side=tk.RIGHT, padx=4)
        ttk.Button(
            button_frame,
            text="Evet",
            command=lambda: (result.update({"value": True}), dialog.destroy()),
        ).pack(side=tk.RIGHT, padx=4)
    else:
        ttk.Button(button_frame, text="Tamam", command=dialog.destroy).pack(side=tk.RIGHT, padx=4)

    dialog.update_idletasks()
    _center_window(dialog, parent)
    dialog.wait_window()
    return result["value"]


def show_info(parent, title, message):
    _build_dialog(parent, title, message, variant="info", confirm=False)


def show_warning(parent, title, message):
    _build_dialog(parent, title, message, variant="warning", confirm=False)


def show_error(parent, title, message):
    _build_dialog(parent, title, message, variant="error", confirm=False)


def ask_confirm(parent, title, message):
    return _build_dialog(parent, title, message, variant="confirm", confirm=True)


def show_toast(parent, message, duration_ms=2000):
    toast = tk.Toplevel(parent)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.configure(bg="#0f172a")

    label = tk.Label(
        toast,
        text=message,
        bg="#0f172a",
        fg="#ffffff",
        padx=12,
        pady=6,
        font=("Segoe UI", 10),
    )
    label.pack()

    toast.update_idletasks()
    _center_window(toast, parent)
    toast.after(duration_ms, toast.destroy)
