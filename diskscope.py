import os
import csv
import shutil
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

APP_NAME = "DiskScope"
BG = "#0b1220"
PANEL = "#131f32"
PANEL2 = "#1b2b43"
TEXT = "#edf4ff"
MUTED = "#9bb0cc"
ACCENT = "#48d6a2"
BLUE = "#62a5ff"
PURPLE = "#c3a0ff"
ORANGE = "#ffbd72"
RED = "#ff6b78"

def fmt_size(size):
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024

class DiskScope:
    def __init__(self, root):
        self.root = root
        root.title("DiskScope V5 — Disk Space Analyzer")
        root.geometry("1180x780")
        root.minsize(900, 620)
        root.configure(bg=BG)
        self.events = queue.Queue()
        self.scanning = False
        self.current_path = ""
        self.folder_rows = []   # (size_bytes, file_count, path)
        self.file_rows = []     # (size_bytes, name, path)
        self._style()
        self._ui()
        self._load_drives()
        root.after(100, self._poll)

    def _style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Treeview", background=PANEL, foreground=TEXT,
                    fieldbackground=PANEL, rowheight=30, borderwidth=0,
                    font=("Segoe UI", 10))
        s.configure("Treeview.Heading", background=PANEL2, foreground=TEXT,
                    relief="flat", font=("Segoe UI", 10, "bold"))
        s.map("Treeview", background=[("selected", "#2458a6")],
              foreground=[("selected", "#ffffff")])
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=PANEL2, foreground=TEXT,
                    padding=(18, 10), font=("Segoe UI", 10, "bold"))
        s.map("TNotebook.Tab", background=[("selected", "#285a8f")],
              foreground=[("selected", "#ffffff")])
        s.configure("TProgressbar", troughcolor=PANEL2, background=ACCENT, thickness=8)

    def label(self, parent, text, size=10, color=TEXT, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"), **kwargs)

    def button(self, parent, text, command, color=PANEL2):
        return tk.Button(parent, text=text, command=command, bg=color, fg=TEXT,
                         activebackground="#31527a", activeforeground=TEXT,
                         relief="flat", bd=0, padx=13, pady=9,
                         font=("Segoe UI", 9, "bold"), cursor="hand2")

    def _ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=24, pady=(20, 14))
        self.label(header, "◈  DiskScope", 25, TEXT, True).pack(side="left")
        self.label(header, "V5  /  DISK SPACE ANALYZER", 10, MUTED, True).pack(side="left", padx=16, pady=(9, 0))
        self.status = self.label(header, "● READY", 10, ACCENT, True)
        self.status.pack(side="right", pady=(9, 0))

        controls = tk.Frame(self.root, bg=PANEL, padx=15, pady=14)
        controls.pack(fill="x", padx=24, pady=(0, 12))
        self.label(controls, "LOCATION", 9, MUTED, True).pack(side="left", padx=(0, 10))
        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(controls, textvariable=self.drive_var, width=13, state="readonly")
        self.drive_combo.pack(side="left", padx=(0, 8))
        self.drive_combo.bind("<<ComboboxSelected>>", self._drive_selected)
        self.button(controls, "Browse folder", self._browse).pack(side="left", padx=4)
        self.scan_btn = self.button(controls, "▶  Analyze", self._scan, "#246fe5")
        self.scan_btn.pack(side="left", padx=4)
        self.button(controls, "Export CSV", self._export).pack(side="right", padx=4)

        self.breadcrumb = tk.Frame(self.root, bg="#0e1a2b", padx=14, pady=9)
        self.breadcrumb.pack(fill="x", padx=24, pady=(0, 12))
        self.label(self.breadcrumb, "CURRENT LOCATION", 9, MUTED, True).pack(side="left")
        self.breadcrumb_path = self.label(self.breadcrumb, "Not selected", 10, ACCENT, True, anchor="w")
        self.breadcrumb_path.pack(side="left", fill="x", expand=True, padx=12)
        self.button(self.breadcrumb, "Open in Explorer", self._open_current_location).pack(side="right")

        cards = tk.Frame(self.root, bg=BG)
        cards.pack(fill="x", padx=24, pady=(0, 10))
        self.metrics = []
        for title, accent in [("SCANNED SIZE", ACCENT), ("FILES FOUND", BLUE),
                              ("FOLDERS FOUND", PURPLE), ("SKIPPED / ERRORS", ORANGE)]:
            card = tk.Frame(cards, bg=PANEL, padx=14, pady=12,
                            highlightbackground="#273851", highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=(0, 9))
            self.label(card, title, 9, MUTED, True).pack(anchor="w")
            val = self.label(card, "—", 19, accent, True)
            val.pack(anchor="w", pady=(5, 0))
            self.metrics.append(val)

        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", padx=24, pady=(0, 5))
        self.progress_text = self.label(self.root, "Choose a drive or folder, then click Analyze.", 9, MUTED)
        self.progress_text.pack(anchor="w", padx=25, pady=(0, 10))

        # Full-width navigation buttons; content panes switch below them.
        self.tab_shell = tk.Frame(self.root, bg=BG)
        self.tab_shell.pack(fill="both", expand=True, padx=24, pady=(0, 14))
        self.nav = tk.Frame(self.tab_shell, bg=BG)
        self.nav.pack(fill="x", pady=(0, 0))
        self.folder_tab = tk.Frame(self.tab_shell, bg=PANEL)
        self.files_tab = tk.Frame(self.tab_shell, bg=PANEL)
        self.map_tab = tk.Frame(self.tab_shell, bg=PANEL)
        self._make_folder_tab()
        self._make_files_tab()
        self._make_map_tab()
        self.tab_buttons = []
        for title, pane in [("Folder Breakdown", self.folder_tab),
                            ("Files & Actions", self.files_tab),
                            ("Folder Usage", self.map_tab)]:
            b = tk.Button(self.nav, text=title, command=lambda p=pane, t=title: self._show_tab(p, t),
                          bg=PANEL2, fg=TEXT, activebackground="#285a8f",
                          activeforeground=TEXT, relief="flat", bd=0,
                          font=("Segoe UI", 10, "bold"), pady=12, cursor="hand2")
            b.pack(side="left", fill="x", expand=True, padx=(0, 4))
            self.tab_buttons.append((b, pane, title))
        self._show_tab(self.folder_tab, "Folder Breakdown")

        footer = tk.Frame(self.root, bg=BG)
        footer.pack(fill="x", padx=24, pady=(0, 12))
        self.label(footer, "Read-only scan until you explicitly choose Move or Delete • No automatic cleanup", 9, MUTED).pack(side="left")
        self.path_label = self.label(footer, "No location selected", 9, MUTED)
        self.path_label.pack(side="right")

    def _show_tab(self, pane, title):
        for p in (self.folder_tab, self.files_tab, self.map_tab):
            p.pack_forget()
        pane.pack(fill="both", expand=True)
        for b, p, t in self.tab_buttons if hasattr(self, "tab_buttons") else []:
            b.configure(bg="#285a8f" if p is pane else PANEL2)
        if hasattr(self, "tab_buttons"):
            self.progress_text.config(text=f"Viewing: {title}")

    def _make_folder_tab(self):
        self.label(self.folder_tab, "All scanned folders · largest first", 12, TEXT, True).pack(anchor="w", padx=15, pady=13)
        frame = tk.Frame(self.folder_tab, bg=PANEL)
        frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.folder_tree = ttk.Treeview(frame, columns=("size", "files", "path"), show="headings")
        for col, title, width, anchor in [
            ("size", "TOTAL SIZE", 130, "e"), ("files", "FILES", 90, "center"),
            ("path", "FOLDER PATH", 650, "w")]:
            self.folder_tree.heading(col, text=title)
            self.folder_tree.column(col, width=width, anchor=anchor)
        ys = ttk.Scrollbar(frame, orient="vertical", command=self.folder_tree.yview)
        xs = ttk.Scrollbar(frame, orient="horizontal", command=self.folder_tree.xview)
        self.folder_tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.folder_tree.grid(row=0, column=0, sticky="nsew")
        self.folder_tree.bind("<Double-1>", self._open_selected_folder)
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)

    def _make_files_tab(self):
        top = tk.Frame(self.files_tab, bg=PANEL)
        top.pack(fill="x", padx=14, pady=12)
        self.label(top, "Largest files found · select one or more rows", 12, TEXT, True).pack(side="left")
        self.label(top, "Tip: Ctrl-click for multiple selection", 9, MUTED).pack(side="right")
        frame = tk.Frame(self.files_tab, bg=PANEL)
        frame.pack(fill="both", expand=True, padx=14)
        self.file_tree = ttk.Treeview(frame, columns=("size", "name", "path"), show="headings", selectmode="extended")
        for col, title, width, anchor in [
            ("size", "SIZE", 120, "e"), ("name", "FILE NAME", 230, "w"),
            ("path", "FULL PATH", 650, "w")]:
            self.file_tree.heading(col, text=title)
            self.file_tree.column(col, width=width, anchor=anchor)
        ys = ttk.Scrollbar(frame, orient="vertical", command=self.file_tree.yview)
        xs = ttk.Scrollbar(frame, orient="horizontal", command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.file_tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)
        self.file_tree.bind("<Double-1>", lambda _e: self._open_selected_file())
        actions = tk.Frame(self.files_tab, bg=PANEL)
        actions.pack(fill="x", padx=14, pady=12)
        self.button(actions, "Open selected file", self._open_selected_file, "#246fe5").pack(side="left", padx=(0, 8))
        self.button(actions, "Open containing folder", self._open_selected_file_folder, "#285a8f").pack(side="left", padx=4)
        self.button(actions, "Move selected…", self._move_selected, "#285a8f").pack(side="left", padx=4)
        self.button(actions, "Delete selected", self._delete_selected, "#8f2f42").pack(side="left", padx=4)
        self.label(actions, "Select rows first · Delete is permanent", 9, ORANGE).pack(side="right")

    def _make_map_tab(self):
        self.label(self.map_tab, "Folder Usage · percentage of selected directory", 12, TEXT, True).pack(anchor="w", padx=15, pady=(13, 4))
        self.map_note = self.label(self.map_tab, "Analyze a location to compare its largest folders.", 9, MUTED)
        self.map_note.pack(anchor="w", padx=15, pady=(0, 8))
        chart_frame = tk.Frame(self.map_tab, bg=PANEL)
        chart_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.usage_canvas = tk.Canvas(chart_frame, bg="#0d1727", highlightthickness=0)
        self.usage_scroll = ttk.Scrollbar(chart_frame, orient="vertical", command=self.usage_canvas.yview)
        self.usage_inner = tk.Frame(self.usage_canvas, bg="#0d1727")
        self.usage_inner.bind("<Configure>", lambda _e: self.usage_canvas.configure(scrollregion=self.usage_canvas.bbox("all")))
        self.usage_canvas.create_window((0, 0), window=self.usage_inner, anchor="nw", tags="usage_inner")
        self.usage_canvas.configure(yscrollcommand=self.usage_scroll.set)
        self.usage_canvas.pack(side="left", fill="both", expand=True)
        self.usage_scroll.pack(side="right", fill="y")
        self.usage_canvas.bind("<Configure>", lambda e: self.usage_canvas.itemconfigure("usage_inner", width=e.width))
        self.map_items = []

    def _load_drives(self):
        if os.name == "nt":
            vals = [c + ":\\" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(c + ":\\")]
        else:
            vals = ["/"]
        self.drive_combo["values"] = vals
        if vals:
            self.drive_combo.current(0)
            self._set_current_path(vals[0])

    def _set_current_path(self, path):
        self.current_path = os.path.abspath(path) if path else ""
        self.path_label.config(text=self.current_path or "No location selected")
        self.breadcrumb_path.config(text=self.current_path or "Not selected")
        # Keep the drive selector in sync with the chosen drive when possible.
        if os.name == "nt" and self.current_path:
            drive = os.path.splitdrive(self.current_path)[0] + "\\"
            values = list(self.drive_combo["values"])
            if drive in values:
                self.drive_var.set(drive)

    def _drive_selected(self, _event=None):
        self._set_current_path(self.drive_var.get())

    def _browse(self):
        p = filedialog.askdirectory(title="Choose folder to analyze",
                                    initialdir=self.current_path or None)
        if p:
            self._set_current_path(p)

    def _open_current_location(self):
        if not self.current_path or not os.path.isdir(self.current_path):
            messagebox.showinfo("No location", "Choose a valid drive or folder first.")
            return
        try:
            if os.name == "nt":
                os.startfile(self.current_path)
            else:
                messagebox.showinfo("Current location", self.current_path)
        except OSError as e:
            messagebox.showerror("Could not open location", str(e))

    def _scan(self):
        if self.scanning:
            return
        path = self.current_path
        if not path or not os.path.isdir(path):
            messagebox.showwarning("Choose a location", "Please select a valid drive or folder.")
            return
        self.scanning = True
        self.scan_btn.config(state="disabled")
        self.status.config(text="● SCANNING", fg=ORANGE)
        self.progress.start(10)
        self.progress_text.config(text="Scanning all accessible folders and files…")
        for tree in (self.folder_tree, self.file_tree):
            tree.delete(*tree.get_children())
        for metric in self.metrics:
            metric.config(text="Scanning…")
        self.folder_rows, self.file_rows = [], []
        # V5 replaced the old treemap canvas with the Folder Usage chart.
        # Clear the chart safely before starting a new scan.
        if hasattr(self, "usage_inner"):
            for child in self.usage_inner.winfo_children():
                child.destroy()
        if hasattr(self, "map_note"):
            self.map_note.config(text="Scanning folders to calculate usage percentages…")
        threading.Thread(target=self._worker, args=(path,), daemon=True).start()

    def _worker(self, root_path):
        direct_sizes, direct_counts = {}, {}
        file_rows = []
        total_size = total_files = total_folders = errors = 0
        try:
            for current, dirs, files in os.walk(root_path, topdown=True):
                dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(current, d))]
                total_folders += len(dirs)
                size_here = count_here = 0
                for name in files:
                    path = os.path.join(current, name)
                    try:
                        if os.path.islink(path):
                            continue
                        size = os.path.getsize(path)
                        size_here += size
                        count_here += 1
                        total_size += size
                        total_files += 1
                        file_rows.append((size, name, path))
                    except OSError:
                        errors += 1
                direct_sizes[current] = size_here
                direct_counts[current] = count_here
                if total_files % 300 == 0 and total_files:
                    self.events.put(("progress", total_files, total_folders, errors))
            # Aggregate child sizes/counts into parents so every nested folder is represented.
            sizes = dict(direct_sizes)
            counts = dict(direct_counts)
            for folder in sorted(sizes, key=lambda p: p.count(os.sep), reverse=True):
                parent = os.path.dirname(folder)
                if parent in sizes and parent != folder:
                    sizes[parent] += sizes[folder]
                    counts[parent] += counts[folder]
            folders = [(sizes[p], counts[p], p) for p in sizes]
            folders.sort(key=lambda x: x[0], reverse=True)
            file_rows.sort(key=lambda x: x[0], reverse=True)
            self.events.put(("done", root_path, total_size, total_files, total_folders, errors, folders, file_rows[:500]))
        except Exception as e:
            self.events.put(("failed", str(e)))

    def _poll(self):
        try:
            while True:
                e = self.events.get_nowait()
                if e[0] == "progress":
                    _, f, d, er = e
                    self.progress_text.config(text=f"Scanned {f:,} files · {d:,} folders · {er:,} skipped/errors")
                elif e[0] == "done":
                    _, root, size, nf, nd, err, folders, files = e
                    self.scanning = False
                    self.progress.stop()
                    self.scan_btn.config(state="normal")
                    self.status.config(text="● SCAN COMPLETE", fg=ACCENT)
                    for label, value in zip(self.metrics, [fmt_size(size), f"{nf:,}", f"{nd:,}", f"{err:,}"]):
                        label.config(text=value)
                    self.progress_text.config(text=f"Finished: {root}  |  {nf:,} files scanned")
                    self.folder_rows, self.file_rows = folders, files
                    for size, count, path in folders:
                        self.folder_tree.insert("", "end", values=(fmt_size(size), f"{count:,}", path))
                    for size, name, path in files:
                        self.file_tree.insert("", "end", values=(fmt_size(size), name, path))
                    self._draw_map()
                elif e[0] == "failed":
                    self.scanning = False; self.progress.stop(); self.scan_btn.config(state="normal")
                    self.status.config(text="● SCAN FAILED", fg=RED)
                    messagebox.showerror("Scan failed", e[1])
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _draw_map(self):
        """Render a readable horizontal percentage bar for each major folder."""
        if not hasattr(self, "usage_inner"):
            return
        for child in self.usage_inner.winfo_children():
            child.destroy()
        if not self.folder_rows:
            self.map_note.config(text="Analyze a location to see folder storage percentages.")
            return
        root_size = max((size for size, _count, path in self.folder_rows if os.path.normcase(path) == os.path.normcase(self.current_path)), default=0)
        if not root_size:
            root_size = max((r[0] for r in self.folder_rows), default=1)
        # Only direct children of the selected scan root; if none found, show top non-root folders.
        root = os.path.normcase(os.path.abspath(self.current_path))
        children = []
        for size, count, path in self.folder_rows:
            ap = os.path.normcase(os.path.abspath(path))
            if ap == root:
                continue
            if os.path.dirname(ap) == root:
                children.append((size, count, path))
        if not children:
            children = [r for r in self.folder_rows if os.path.normcase(os.path.abspath(r[2])) != root][:30]
        children.sort(key=lambda r: r[0], reverse=True)
        self.map_note.config(text=f"Folder percentages are relative to {self.current_path}. Showing up to 50 folders.")
        palette = ["#48d6a2", "#62a5ff", "#c3a0ff", "#ffbd72", "#ff6b78"]
        for i, (size, count, path) in enumerate(children[:50]):
            pct = (size / root_size * 100) if root_size else 0
            row = tk.Frame(self.usage_inner, bg="#0d1727", padx=10, pady=8)
            row.pack(fill="x", pady=3)
            name = os.path.basename(path.rstrip("\\\\/")) or path
            name_lbl = tk.Label(row, text=name, bg="#0d1727", fg=TEXT,
                                font=("Segoe UI", 10, "bold"), anchor="w", width=28)
            name_lbl.pack(side="left")
            bar_bg = tk.Frame(row, bg="#24364e", height=18)
            bar_bg.pack(side="left", fill="x", expand=True, padx=10)
            bar_bg.pack_propagate(False)
            fill = tk.Frame(bar_bg, bg=palette[i % len(palette)], height=18)
            fill.place(x=0, y=0, relwidth=min(1.0, max(0.0, pct/100)), relheight=1)
            tk.Label(row, text=f"{pct:.1f}%  ·  {fmt_size(size)}  ·  {count:,} files",
                     bg="#0d1727", fg=MUTED, font=("Segoe UI", 9), width=31, anchor="e").pack(side="right")
            # Click the folder name to open the actual folder in Explorer.
            for widget in (row, name_lbl):
                widget.bind("<Double-Button-1>", lambda _e, folder=path: self._open_folder_path(folder))
        self.usage_inner.update_idletasks()

    def _open_folder_path(self, path):
        if not os.path.isdir(path):
            messagebox.showinfo("Folder unavailable", "This folder is no longer available.")
            return
        try:
            if os.name == "nt":
                os.startfile(path)
            else:
                messagebox.showinfo("Folder path", path)
        except OSError as e:
            messagebox.showerror("Could not open folder", str(e))

    def _open_selected_folder(self, _event=None):
        sel = self.folder_tree.selection()
        if not sel:
            return
        path = self.folder_tree.item(sel[0], "values")[2]
        self._open_folder_path(path)

    def _open_selected_file(self):
        paths = self._selected_paths()
        if not paths:
            messagebox.showinfo("Select files", "Select one or more files first.")
            return
        path = paths[0]
        try:
            if os.path.isfile(path) and os.name == "nt":
                os.startfile(path)
            elif os.path.isfile(path):
                messagebox.showinfo("Selected file", path)
            else:
                messagebox.showwarning("File unavailable", "The selected file no longer exists.")
        except OSError as e:
            messagebox.showerror("Could not open file", str(e))

    def _open_selected_file_folder(self):
        paths = self._selected_paths()
        if not paths:
            messagebox.showinfo("Select files", "Select one or more files first.")
            return
        self._open_folder_path(os.path.dirname(paths[0]))

    def _selected_paths(self):
        selected = self.file_tree.selection()
        return [self.file_tree.item(item, "values")[2] for item in selected]

    def _delete_selected(self):
        paths = self._selected_paths()
        if not paths:
            messagebox.showinfo("Select files", "Select one or more files in the table first.")
            return
        if not messagebox.askyesno("Confirm permanent deletion",
                f"Delete {len(paths)} selected file(s) permanently?\\n\\nThis cannot be undone."):
            return
        deleted, failed = 0, []
        for path in paths:
            try:
                os.remove(path)
                deleted += 1
            except OSError as e:
                failed.append(f"{path}: {e}")
        messagebox.showinfo("Delete result", f"Deleted: {deleted}\\nFailed: {len(failed)}" +
                            (("\\n\\n" + "\\n".join(failed[:4])) if failed else ""))
        self._scan()

    def _move_selected(self):
        paths = self._selected_paths()
        if not paths:
            messagebox.showinfo("Select files", "Select one or more files in the table first.")
            return
        dest = filedialog.askdirectory(title="Choose destination folder")
        if not dest:
            return
        moved, failed = 0, []
        for path in paths:
            try:
                target = os.path.join(dest, os.path.basename(path))
                if os.path.exists(target):
                    failed.append(f"{os.path.basename(path)}: destination already has this name")
                    continue
                shutil.move(path, target)
                moved += 1
            except OSError as e:
                failed.append(f"{path}: {e}")
        messagebox.showinfo("Move result", f"Moved: {moved}\\nSkipped/failed: {len(failed)}" +
                            (("\\n\\n" + "\\n".join(failed[:4])) if failed else ""))
        self._scan()

    def _export(self):
        if not self.folder_rows and not self.file_rows:
            messagebox.showinfo("No report", "Run an analysis first.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"diskscope_report_{datetime.now():%Y%m%d_%H%M}.csv")
        if not filename:
            return
        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["DiskScope V5 Report", datetime.now().isoformat(timespec="seconds")])
                writer.writerow(["Folder Breakdown"])
                writer.writerow(["Size", "File count", "Folder path"])
                writer.writerows([[fmt_size(s), c, p] for s, c, p in self.folder_rows])
                writer.writerow([])
                writer.writerow(["Largest Files"])
                writer.writerow(["Size", "File name", "Full path"])
                writer.writerows([[fmt_size(s), n, p] for s, n, p in self.file_rows])
            messagebox.showinfo("Export complete", f"Saved report to:\\n{filename}")
        except OSError as e:
            messagebox.showerror("Export failed", str(e))

def main():
    root = tk.Tk()
    DiskScope(root)
    root.mainloop()

if __name__ == "__main__":
    main()
