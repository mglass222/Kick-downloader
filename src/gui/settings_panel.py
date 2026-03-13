"""Settings panel widget for poll interval and output directory."""

from __future__ import annotations

from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from ..config import Settings


class SettingsPanel(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        settings: Settings,
        on_change: Callable[[Settings], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._settings = settings
        self._on_change = on_change

        label = ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(weight="bold"))
        label.pack(anchor="w", padx=8, pady=(4, 0))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=(0, 8))

        # Poll interval
        ctk.CTkLabel(row, text="Poll interval (sec):").pack(side="left", padx=(0, 4))
        self._interval_var = ctk.StringVar(value=str(settings.poll_interval_seconds))
        self._interval_entry = ctk.CTkEntry(row, textvariable=self._interval_var, width=70)
        self._interval_entry.pack(side="left", padx=(0, 12))
        self._interval_entry.bind("<FocusOut>", lambda _: self._apply())
        self._interval_entry.bind("<Return>", lambda _: self._apply())

        # Output dir
        ctk.CTkLabel(row, text="Output dir:").pack(side="left", padx=(0, 4))
        self._dir_var = ctk.StringVar(value=settings.output_dir)
        self._dir_entry = ctk.CTkEntry(row, textvariable=self._dir_var, width=200)
        self._dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._dir_entry.bind("<FocusOut>", lambda _: self._apply())
        self._dir_entry.bind("<Return>", lambda _: self._apply())

        self._browse_btn = ctk.CTkButton(
            row, text="Browse...", width=80, command=self._browse
        )
        self._browse_btn.pack(side="left")

    def _browse(self) -> None:
        path = filedialog.askdirectory(initialdir=self._settings.output_dir)
        if path:
            self._dir_var.set(path)
            self._apply()

    def _apply(self) -> None:
        try:
            interval = int(self._interval_var.get())
            if interval < 10:
                interval = 10
        except ValueError:
            interval = self._settings.poll_interval_seconds

        self._settings.poll_interval_seconds = interval
        self._settings.output_dir = self._dir_var.get().strip() or self._settings.output_dir
        self._on_change(self._settings)
