"""Add streamer input bar widget."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk


class AddStreamerBar(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_add: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_add = on_add

        label = ctk.CTkLabel(self, text="Add Streamer", font=ctk.CTkFont(weight="bold"))
        label.pack(anchor="w", padx=8, pady=(4, 0))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkLabel(row, text="Channel slug:").pack(side="left", padx=(0, 4))
        self._entry = ctk.CTkEntry(row, placeholder_text="e.g. xqc")
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._entry.bind("<Return>", lambda _: self._submit())

        self._btn = ctk.CTkButton(row, text="Add", width=60, command=self._submit)
        self._btn.pack(side="left")

    def _submit(self) -> None:
        slug = self._entry.get().strip()
        if slug:
            self._on_add(slug)
            self._entry.delete(0, "end")
