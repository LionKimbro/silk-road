import os
import platform
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from silkroad import app
from silkroad import constants as C
from silkroad.config import save_config
from silkroad.sherpa_files import load_sherpa, save_sherpa_record

g = {
    "root": None,
    "execroot": None,
    "config": None,
    "state": None,
    "widgets": {},
}


def run():
    root = tk.Tk()
    g["root"] = root
    g["execroot"] = app.g["execroot"]
    g["config"] = {"waystations": app.g["settings"]["known_waystations"], "waypoints": app.g["settings"]["known_waystations"], "settings": app.g["settings"]}
    root.title("Silk Road")
    root.geometry(app.g["settings"].get("window_geometry", "1280x760"))
    build_ui(root)
    refresh_all()
    schedule_tick()
    root.mainloop()


def build_ui(root):
    g["widgets"] = {}
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    paned = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
    paned.grid(row=0, column=0, sticky="nsew")
    left = ttk.Frame(paned, padding=8)
    middle = ttk.Frame(paned, padding=8)
    right = ttk.Frame(paned, padding=8)
    paned.add(left, weight=1)
    paned.add(middle, weight=1)
    paned.add(right, weight=3)
    build_waystation_pane(left)
    build_sherpa_pane(middle)
    build_editor_pane(right)
    status = ttk.Label(root, text="Ready.", anchor="w")
    status.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
    g["widgets"]["status"] = status
    g["widgets"]["result"] = status


def build_waystation_pane(parent):
    parent.columnconfigure(0, weight=1)
    ttk.Label(parent, text="WAYSTATIONS", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
    tree = ttk.Treeview(parent, columns=("name", "source", "path", "sherpas", "hiking", "warnings"), show="headings", height=20)
    for col, width in [("name", 150), ("source", 80), ("path", 250), ("sherpas", 60), ("hiking", 60), ("warnings", 70)]:
        tree.heading(col, text=col.title())
        tree.column(col, width=width, anchor="w")
    tree.grid(row=1, column=0, sticky="nsew", pady=6)
    parent.rowconfigure(1, weight=1)
    tree.bind("<<TreeviewSelect>>", on_waystation_selected)
    g["widgets"]["waystations"] = tree
    g["widgets"]["waypoints"] = tree
    buttons = ttk.Frame(parent)
    buttons.grid(row=2, column=0, sticky="ew")
    ttk.Button(buttons, text="Add", command=show_add_waystation).grid(row=0, column=0, padx=(0, 4))
    ttk.Button(buttons, text="Create", command=show_create_waystation).grid(row=0, column=1, padx=4)
    ttk.Button(buttons, text="Discover", command=discover_waystations).grid(row=0, column=2, padx=4)
    ttk.Button(buttons, text="Open", command=open_selected_waystation).grid(row=0, column=3, padx=4)
    ttk.Button(buttons, text="Remove", command=remove_selected_waypoint).grid(row=0, column=4, padx=4)


def build_sherpa_pane(parent):
    parent.columnconfigure(0, weight=1)
    ttk.Label(parent, text="SHERPAS", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
    tree = ttk.Treeview(parent, columns=("enabled", "name", "status", "current"), show="headings", height=20)
    for col, width in [("enabled", 70), ("name", 160), ("status", 150), ("current", 240)]:
        tree.heading(col, text=col.title())
        tree.column(col, width=width, anchor="w")
    tree.grid(row=1, column=0, sticky="nsew", pady=6)
    parent.rowconfigure(1, weight=1)
    tree.bind("<<TreeviewSelect>>", on_sherpa_selected)
    tree.bind("<Double-1>", toggle_selected_sherpa_enabled)
    g["widgets"]["sherpas"] = tree
    buttons = ttk.Frame(parent)
    buttons.grid(row=2, column=0, sticky="ew")
    ttk.Button(buttons, text="Run", command=run_selected_sherpa).grid(row=0, column=0, padx=(0, 4))
    ttk.Button(buttons, text="Pause", command=pause_selected_sherpa).grid(row=0, column=1, padx=4)
    ttk.Button(buttons, text="Resume", command=resume_selected_sherpa).grid(row=0, column=2, padx=4)
    ttk.Button(buttons, text="Abandon", command=abandon_selected_sherpa).grid(row=0, column=3, padx=4)


def build_editor_pane(parent):
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(1, weight=1)
    ttk.Label(parent, text="SELECTED SHERPA", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
    canvas = tk.Canvas(parent, borderwidth=0, highlightthickness=0)
    scroll = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    frame = ttk.Frame(canvas, padding=(0, 4, 10, 4))
    frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.grid(row=1, column=0, sticky="nsew")
    scroll.grid(row=1, column=1, sticky="ns")
    g["widgets"]["editor_frame"] = frame


def refresh_all():
    ensure_app_ready_from_ui_state()
    refresh_waystations()
    refresh_sherpas()
    refresh_editor()
    if "status" in g["widgets"]:
        g["widgets"]["status"].configure(text=app.g.get("status", "Ready."))


def refresh_waystations():
    tree = g["widgets"].get("waystations")
    if not tree:
        return
    selected = app.g.get("selected_waystation")
    tree.delete(*tree.get_children())
    for row in app.waystation_rows():
        iid = row["path"]
        tree.insert("", "end", iid=iid, values=(row["name"], row["source"], row["path"], row["sherpa_count"], row["hiking_count"], row["warnings"]))
    if selected and tree.exists(selected):
        tree.selection_set(selected)
        tree.focus(selected)


def refresh_sherpas():
    tree = g["widgets"].get("sherpas")
    if not tree:
        return
    selected = app.g.get("selected_sherpa")
    tree.delete(*tree.get_children())
    for row in app.sherpa_rows():
        state = row["state"]
        control = row["control"]
        status = state.get("status", C.STATUS_RESTING)
        enabled = "[x]" if control.get("enabled", True) else "[ ]"
        tree.insert("", "end", iid=row["sherpa_id"], values=(enabled, row["spec"].get("name", row["sherpa_id"]), C.STATUS_TEXT.get(status, status), state.get("current_directory") or ""))
    if selected and tree.exists(selected):
        tree.selection_set(selected)
        tree.focus(selected)


def refresh_editor():
    frame = g["widgets"].get("editor_frame")
    if not frame:
        return
    for child in frame.winfo_children():
        child.destroy()
    record = app.selected_sherpa_record()
    if not record:
        ttk.Label(frame, text="No Sherpa selected.").grid(row=0, column=0, sticky="w")
        return
    make_editor_sections(frame, record)


def make_editor_sections(parent, record):
    row = 0
    row = section_identity(parent, record, row)
    row = section_navigation(parent, record, row)
    row = section_noticing(parent, record, row)
    row = section_library(parent, record, row)
    row = section_journal(parent, record, row)
    row = section_pace(parent, record, row)
    section_current_journey(parent, record, row)


def section(parent, title, row):
    box = ttk.LabelFrame(parent, text=title, padding=8)
    box.grid(row=row, column=0, sticky="ew", pady=(0, 8))
    box.columnconfigure(1, weight=1)
    return box


def section_identity(parent, record, row):
    box = section(parent, "Identity and Status", row)
    spec = record["spec"]
    state = record["state"]
    control = record["control"]
    add_label(box, 0, "Name", spec.get("name"))
    add_label(box, 1, "Sherpa ID", record["sherpa_id"])
    add_label(box, 2, "Hosting Waystation", app.g.get("selected_waystation"))
    add_label(box, 3, "Enabled", str(bool(control.get("enabled", True))))
    add_label(box, 4, "Current Status", C.STATUS_TEXT.get(state.get("status"), state.get("status")))
    add_label(box, 5, "Last Error", state.get("last_error") or "")
    return row + 1


def section_navigation(parent, record, row):
    box = section(parent, "Navigation", row)
    nav = record["spec"].setdefault("navigation", {})
    add_label(box, 0, "Mode", nav.get("mode"))
    add_label(box, 1, "Peer Depth", nav.get("peer_depth", ""))
    add_label(box, 2, "Levels Up / Down", f"{nav.get('levels_up', '')} / {nav.get('levels_down', '')}")
    add_label(box, 3, "Specific Path", nav.get("path", ""))
    ttk.Button(box, text="Open Territory", command=open_territory).grid(row=4, column=0, sticky="w", pady=(6, 0))
    return row + 1


def section_noticing(parent, record, row):
    box = section(parent, "Noticing", row)
    noticing = record["spec"].get("noticing", {})
    labels = [
        ("Waystations", "waystations"),
        ("Lion JSON Documents", "lion_json_documents"),
        ("Annotated Markdown", "annotated_markdown_documents"),
        ("File Pattern", "file_pattern"),
    ]
    for index, pair in enumerate(labels):
        label, key = pair
        cfg = noticing.get(key, {})
        text = f"notice={cfg.get('enabled')} register={cfg.get('register', '')} collect={cfg.get('collect', '')} journal={cfg.get('journal', '')}"
        add_label(box, index, label, text)
    return row + 1


def section_library(parent, record, row):
    box = section(parent, "Library and Collection", row)
    add_label(box, 0, "Discovery Library", record["spec"].get("library", {}).get("target", "waystation"))
    add_label(box, 1, "Waystation Library", str(Path(app.g["selected_waystation"]) / "libraries" / "library.jsonl"))
    ttk.Button(box, text="Open Library", command=open_library).grid(row=2, column=0, sticky="w", pady=(6, 0))
    return row + 1


def section_journal(parent, record, row):
    box = section(parent, "Journal", row)
    journal = record["spec"].get("journal", {})
    add_label(box, 0, "Enabled", journal.get("enabled", True))
    add_label(box, 1, "Detail", journal.get("detail", "summary"))
    ttk.Button(box, text="Open Journals", command=open_journals).grid(row=2, column=0, sticky="w", pady=(6, 0))
    return row + 1


def section_pace(parent, record, row):
    box = section(parent, "Pace and Schedule", row)
    pace = record["control"].get("pace", {})
    schedule = record["control"].get("schedule", {})
    add_label(box, 0, "Pace", f"{pace.get('preset', 'custom')} - {pace.get('work_budget_ms')} ms every {pace.get('tick_interval_ms')} ms")
    add_label(box, 1, "Automatic Journeys", schedule.get("automatic", False))
    add_label(box, 2, "Journey Interval", f"{schedule.get('journey_interval_seconds', 0)} seconds")
    return row + 1


def section_current_journey(parent, record, row):
    box = section(parent, "Current Journey", row)
    state = record["state"]
    fields = [
        ("Journey", state.get("journey_id")),
        ("Started", state.get("started_at")),
        ("Current Directory", state.get("current_directory")),
        ("Queued Directories", state.get("directories_waiting")),
        ("Visited Directories", state.get("directories_visited")),
        ("Entries Examined", state.get("filesystem_entries_examined")),
        ("Discoveries", state.get("discoveries")),
        ("Warnings", state.get("warnings")),
    ]
    for index, pair in enumerate(fields):
        add_label(box, index, pair[0], pair[1])


def add_label(parent, row, name, value):
    ttk.Label(parent, text=f"{name}:").grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=2)
    ttk.Label(parent, text="" if value is None else str(value), wraplength=560).grid(row=row, column=1, sticky="ew", pady=2)


def on_waystation_selected(event=None):
    tree = g["widgets"]["waystations"]
    sel = tree.selection()
    if sel:
        app.select_waystation(sel[0])
        refresh_sherpas()
        refresh_editor()


def on_sherpa_selected(event=None):
    tree = g["widgets"]["sherpas"]
    sel = tree.selection()
    if sel:
        app.select_sherpa(sel[0])
        refresh_editor()


def toggle_selected_sherpa_enabled(event=None):
    record = app.selected_sherpa_record()
    if not record:
        return
    app.update_control_enabled(record["sherpa_id"], not record["control"].get("enabled", True))
    refresh_all()


def run_selected_sherpa():
    app.run_selected_sherpa()
    refresh_all()


def pause_selected_sherpa():
    app.pause_selected_sherpa()
    refresh_all()


def resume_selected_sherpa():
    app.resume_selected_sherpa()
    refresh_all()


def abandon_selected_sherpa():
    app.abandon_selected_sherpa()
    refresh_all()


def schedule_tick():
    if app.tick_sherpas():
        refresh_all()
    if g.get("root"):
        g["root"].after(250, schedule_tick)


def show_add_waystation():
    path = filedialog.askdirectory(title="Add Waystation")
    if path:
        app.add_waystation(path, Path(path).parent.name)
        refresh_all()


def show_create_waystation():
    path = filedialog.askdirectory(title="Choose parent folder for new Waystation")
    if path:
        target = Path(path) / "waystation"
        app.create_waystation(target, Path(path).name)
        refresh_all()


def discover_waystations():
    app.discover_waystations()
    refresh_all()


def open_selected_waystation():
    if app.g.get("selected_waystation"):
        open_path(app.g["selected_waystation"])


def remove_selected_waypoint():
    tree = g["widgets"].get("waystations")
    if not tree:
        return
    sel = tree.selection()
    if not sel:
        return
    if messagebox.askyesno("Remove Waystation", "Remove this Waystation from the control panel? The folder will not be deleted."):
        app.remove_waystation(sel[0])
        refresh_all()


def open_territory():
    record = app.selected_sherpa_record()
    if not record:
        return
    nav = record["spec"].get("navigation", {})
    if nav.get("mode") == "specific_directory" and nav.get("path"):
        open_path(nav["path"])
    elif app.g.get("selected_waystation"):
        open_path(Path(app.g["selected_waystation"]).parent)


def open_library():
    if app.g.get("selected_waystation"):
        open_path(Path(app.g["selected_waystation"]) / "libraries" / "library.jsonl")


def open_journals():
    record = app.selected_sherpa_record()
    if record:
        open_path(record["paths"]["journal_dir"])


def open_path(path):
    path = str(path)
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def install_waypoint_from_window(window, name_var, path_var):
    ensure_app_ready_from_ui_state()
    app.add_waystation(path_var.get(), name_var.get())
    if g.get("config"):
        g["config"]["waypoints"] = app.g["settings"]["known_waystations"]
        g["config"]["waystations"] = app.g["settings"]["known_waystations"]
    window.destroy()
    refresh_all()


def save_sherpa_code(component, text_widget):
    Path(component).write_text(text_widget.get("1.0", "end-1c"), encoding="utf-8")
    if "status" in g.get("widgets", {}):
        g["widgets"]["status"].configure(text="Saved Sherpa code.")


def save_sherpa_interval(window, sherpa_id, minutes_var):
    ensure_app_ready_from_ui_state()
    record = load_sherpa(app.g["selected_waystation"], sherpa_id) if app.g.get("selected_waystation") else None
    if record:
        minutes = int(minutes_var.get())
        record["control"]["schedule"]["journey_interval_seconds"] = minutes * 60
        record["state"]["next_journey_at"] = "scheduled"
        save_sherpa_record(record)
    if g.get("config"):
        g["config"].setdefault("sherpas", {}).setdefault(sherpa_id, {})["interval_seconds"] = int(minutes_var.get()) * 60
    if g.get("state"):
        g["state"].setdefault("sherpas", {}).setdefault(sherpa_id, {})["next_run"] = "scheduled"
    window.destroy()


def ensure_app_ready_from_ui_state():
    if app.g.get("settings") is not None:
        return
    execroot = g.get("execroot") or Path.cwd()
    app.init(execroot)
    if g.get("config"):
        config = g["config"]
        settings = config.get("settings")
        if settings:
            app.g["settings"] = settings
            if "known_waystations" not in settings:
                settings["known_waystations"] = config.get("waystations") or config.get("waypoints") or []
            app.ensure_configured_waystations()
            app.select_initial_waystation()
