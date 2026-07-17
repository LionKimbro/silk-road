import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

from . import constants as C
from .config import ensure_runtime_dirs, load_config, save_config
from .components import ensure_default_components
from .jsonio import read_json
from .sherpas import dispatch_sherpa, due_to_run, ensure_schedules, compute_next_run
from .state import load_state, save_state
from .waypoints import get_enabled_waypoints, read_waypoint_marker, ensure_waypoint, get_silk_cache_dir


g = {}


def run_gui(execroot):
    ensure_runtime_dirs(execroot)
    ensure_default_components(execroot)
    g["execroot"] = execroot
    g["config"] = load_config(execroot)
    g["state"] = load_state(execroot)
    if ensure_schedules(g["config"], g["state"]):
        save_state(execroot, g["state"])
    g["queue"] = queue.Queue()
    g["worker"] = None
    g["widgets"] = {}

    root = tk.Tk()
    g["root"] = root
    root.title("Silk Road")
    root.geometry("980x620")
    build_ui(root)
    refresh_all()
    root.after(1000, update_cycle)
    root.mainloop()


def build_ui(root):
    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)
    build_menu(root)

    header = ttk.Frame(root, padding=10)
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(0, weight=1)

    title = ttk.Label(header, text="Silk Road", font=("Segoe UI", 18, "bold"))
    title.grid(row=0, column=0, sticky="w")
    run_button = ttk.Button(header, text="Run Document Indexer", command=handle_run_clicked)
    run_button.grid(row=0, column=1, sticky="e")
    g["widgets"]["run_button"] = run_button

    panes = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    panes.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    left = ttk.Frame(panes, padding=6)
    right = ttk.Frame(panes, padding=6)
    panes.add(left, weight=1)
    panes.add(right, weight=2)

    build_waystations(left)
    build_status(right)

    status = ttk.Label(root, text="", anchor="w", padding=(10, 4))
    status.grid(row=2, column=0, sticky="ew")
    g["widgets"]["status"] = status


def build_menu(root):
    menu = tk.Menu(root)
    root.config(menu=menu)

    file_menu = tk.Menu(menu, tearoff=False)
    file_menu.add_command(label="Run Document Indexer", command=handle_run_clicked)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.destroy)
    menu.add_cascade(label="File", menu=file_menu)

    help_menu = tk.Menu(menu, tearoff=False)
    help_menu.add_command(label="Using Silk Road", command=show_usage_help)
    help_menu.add_command(label="Sherpas", command=show_sherpas_help)
    help_menu.add_command(label="Waystation Structure", command=show_waystations_help)
    menu.add_cascade(label="Help", menu=help_menu)


def build_waystations(parent):
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(2, weight=1)

    header = ttk.Frame(parent)
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(0, weight=1)
    ttk.Label(header, text="Waystations", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")

    buttons = ttk.Frame(parent)
    buttons.grid(row=1, column=0, sticky="ew", pady=(6, 0))
    ttk.Button(buttons, text="Install", command=show_install_waystation_window).grid(row=0, column=0, padx=(0, 4))
    ttk.Button(buttons, text="Remove", command=remove_selected_waystation).grid(row=0, column=1, padx=(0, 4))
    ttk.Button(buttons, text="Open", command=open_selected_waystation).grid(row=0, column=2, padx=(0, 4))
    ttk.Button(buttons, text="Refresh", command=refresh_all).grid(row=0, column=3, padx=(0, 4))

    tree = ttk.Treeview(parent, columns=("name", "marker", "path"), show="headings", height=10)
    tree.heading("name", text="Name")
    tree.heading("marker", text="Marker")
    tree.heading("path", text="Path")
    tree.column("name", width=90)
    tree.column("marker", width=70)
    tree.column("path", width=320)
    tree.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
    g["widgets"]["waystations"] = tree
    g["widgets"]["waypoints"] = tree


def build_status(parent):
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(2, weight=1)
    ttk.Label(parent, text="Sherpas", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")

    buttons = ttk.Frame(parent)
    buttons.grid(row=1, column=0, sticky="ew", pady=(6, 0))
    ttk.Button(buttons, text="Run", command=handle_run_clicked).grid(row=0, column=0, padx=(0, 4))
    ttk.Button(buttons, text="Edit Code", command=edit_selected_sherpa_code).grid(row=0, column=1, padx=(0, 4))
    ttk.Button(buttons, text="Interval", command=show_interval_window).grid(row=0, column=2, padx=(0, 4))
    ttk.Button(buttons, text="Logs", command=show_logs_window).grid(row=0, column=3, padx=(0, 4))
    ttk.Button(buttons, text="Failures", command=show_failures_window).grid(row=0, column=4, padx=(0, 4))

    tree = ttk.Treeview(parent, columns=("name", "status", "last", "next", "files", "valid", "dupes", "conflicts", "failures"), show="headings", height=6)
    headings = {
        "name": "Sherpa",
        "status": "Status",
        "last": "Last Run",
        "next": "Next Run",
        "files": "Files",
        "valid": "Valid",
        "dupes": "Dupes",
        "conflicts": "Conflicts",
        "failures": "Failures",
    }
    widths = {
        "name": 130,
        "status": 80,
        "last": 150,
        "next": 150,
        "files": 70,
        "valid": 70,
        "dupes": 70,
        "conflicts": 80,
        "failures": 70,
    }
    for col, text in headings.items():
        tree.heading(col, text=text)
        tree.column(col, width=widths[col], stretch=col in ["last", "next"])
    tree.grid(row=2, column=0, sticky="nsew", pady=(6, 8))
    g["widgets"]["sherpas"] = tree

    ttk.Label(parent, text="Last Result", font=("Segoe UI", 12, "bold")).grid(row=3, column=0, sticky="w")
    text = tk.Text(parent, height=14, wrap="word")
    text.grid(row=4, column=0, sticky="nsew", pady=(6, 0))
    parent.rowconfigure(4, weight=1)
    g["widgets"]["result"] = text


def handle_run_clicked():
    start_sherpa(C.SHERPA_DOCUMENT_INDEXER, "manual")


def start_sherpa(sherpa_name, reason):
    if g.get("worker") and g["worker"].is_alive():
        set_status("A Sherpa is already running.")
        return
    set_status(f"Starting {sherpa_name} ({reason})...")
    g["widgets"]["run_button"].configure(state="disabled")
    worker = threading.Thread(target=run_sherpa_worker, args=(sherpa_name,), daemon=True)
    g["worker"] = worker
    worker.start()
    refresh_all()


def run_sherpa_worker(sherpa_name):
    try:
        result = dispatch_sherpa(g["execroot"], g["config"], g["state"], sherpa_name)
        g["queue"].put({"type": "SHERPA_DONE", "sherpa": sherpa_name, "result": result})
    except Exception as e:
        g["queue"].put({"type": "SHERPA_FAILED", "sherpa": sherpa_name, "error": f"{type(e).__name__}: {e}"})


def update_cycle():
    drain_queue()
    for sherpa_name in [C.SHERPA_DOCUMENT_INDEXER]:
        if due_to_run(g["config"], g["state"], sherpa_name):
            start_sherpa(sherpa_name, "scheduled")
            break
    refresh_all()
    g["root"].after(1000, update_cycle)


def drain_queue():
    while True:
        try:
            event = g["queue"].get_nowait()
        except queue.Empty:
            break
        if event["type"] == "SHERPA_DONE":
            g["state"] = load_state(g["execroot"])
            set_status(f"{event['sherpa']} completed.")
            show_result(event["result"])
            g["widgets"]["run_button"].configure(state="normal")
        elif event["type"] == "SHERPA_FAILED":
            g["state"] = load_state(g["execroot"])
            set_status(f"{event['sherpa']} failed: {event['error']}")
            messagebox.showerror("Silk Road", event["error"])
            g["widgets"]["run_button"].configure(state="normal")


def show_usage_help():
    show_text_window("Using Silk Road", """Silk Road is a local control panel for filesystem Sherpas.

Use Run Document Indexer to scan configured territories for Lion-style JSON documents under docs/raw/.

The scan writes pointer-based indexes into each enabled waystation:

- cache/silk-road/document-index.json
- cache/silk-road/librarian-registry.json
- cache/silk-road/warnings.json
- cache/silk-road/malformed.json
- cache/silk-road/conflicts.json

Runtime configuration and editable Sherpa component code live in .silkroad/.
""")


def show_sherpas_help():
    show_text_window("Sherpas", """Sherpas are small named workers that Silk Road can dispatch.

Version one includes document-indexer. It examines configured territories and explicit document roots, reads JSON files, validates document.document-id, reconciles known locations, and writes waystation indexes.

The default Sherpa code is editable from the GUI. The editor changes the local component file that is executed on the next run:

.silkroad/components/document_indexer.py

The component receives D with config, state, and api, then sets D["result"].
""")


def show_waystations_help():
    show_text_window("Waystation Structure", """A waystation is a recognizable filesystem base for Silk Road state.

Use Install in the Waystations panel to create a waystation at a selected or typed path. The selected folder is the waystation itself; Silk Road does not create a nested waystation folder inside it.

The marker is:

waystation.json

The first waystation structure follows the surviving model:

- signposts/ for neighboring waystations
- cache/ for discovered knowledge
- bazaar/ for wanted and inventory exchange

Silk Road writes its current document index under cache/silk-road/.
""")


def show_text_window(title, content):
    win = tk.Toplevel(g["root"])
    win.title(title)
    win.geometry("720x520")
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=1)
    text = tk.Text(win, wrap="word", padx=10, pady=10)
    text.grid(row=0, column=0, sticky="nsew")
    text.insert("1.0", content)
    text.configure(state="disabled")
    ttk.Button(win, text="Close", command=win.destroy).grid(row=1, column=0, sticky="e", padx=10, pady=10)


def show_install_waystation_window():
    win = tk.Toplevel(g["root"])
    win.title("Install Waystation")
    win.geometry("760x230")
    win.columnconfigure(1, weight=1)

    name_var = tk.StringVar(value="local")
    path_var = tk.StringVar()

    ttk.Label(win, text="Name").grid(row=0, column=0, sticky="w", padx=10, pady=(12, 4))
    ttk.Entry(win, textvariable=name_var).grid(row=0, column=1, sticky="ew", padx=10, pady=(12, 4))

    ttk.Label(win, text="Waystation folder").grid(row=1, column=0, sticky="w", padx=10, pady=4)
    ttk.Entry(win, textvariable=path_var).grid(row=1, column=1, sticky="ew", padx=10, pady=4)
    ttk.Button(win, text="Browse", command=lambda: browse_waystation_path(path_var)).grid(row=1, column=2, padx=10, pady=4)

    note = ttk.Label(
        win,
        text="The selected folder is the waystation itself; Silk Road does not create a nested waystation folder inside it.",
        wraplength=700,
    )
    note.grid(row=2, column=0, columnspan=3, sticky="w", padx=10, pady=(6, 2))

    contents = ttk.Label(
        win,
        text="Install writes waystation.json and ensures signposts/, cache/, and bazaar/ directly in that folder.",
        wraplength=700,
    )
    contents.grid(row=3, column=0, columnspan=3, sticky="w", padx=10, pady=(2, 6))

    actions = ttk.Frame(win)
    actions.grid(row=4, column=0, columnspan=3, sticky="e", padx=10, pady=14)
    ttk.Button(actions, text="Install", command=lambda: install_waystation_from_window(win, name_var, path_var)).grid(row=0, column=0, padx=(0, 4))
    ttk.Button(actions, text="Cancel", command=win.destroy).grid(row=0, column=1)


def browse_waystation_path(path_var):
    path = filedialog.askdirectory(title="Choose waystation folder")
    if path:
        path_var.set(path)


def install_waystation_from_window(win, name_var, path_var):
    name = name_var.get().strip()
    path = path_var.get().strip()
    if not name:
        messagebox.showerror("Silk Road", "Waystation name is required.")
        return
    if not path:
        messagebox.showerror("Silk Road", "Waystation folder path is required.")
        return

    resolved = str(Path(path).expanduser().resolve())
    ensure_waypoint(resolved, name)
    existing = [w for w in g["config"]["waypoints"] if str(Path(w["path"]).expanduser().resolve()).lower() == resolved.lower()]
    if existing:
        existing[0]["name"] = name
        existing[0]["enabled"] = True
    else:
        g["config"]["waypoints"].append({
            "name": name,
            "path": resolved,
            "enabled": True,
        })
    save_config(g["execroot"], g["config"])
    set_status(f"Waystation installed: {resolved}")
    win.destroy()
    refresh_all()


def show_add_waypoint_window():
    show_install_waystation_window()


def add_waypoint_from_window(win, name_var, path_var):
    install_waystation_from_window(win, name_var, path_var)


def show_waypoints_help():
    show_waystations_help()


def show_install_waypoint_window():
    show_install_waystation_window()


def install_waypoint_from_window(win, name_var, path_var):
    install_waystation_from_window(win, name_var, path_var)


def remove_selected_waystation():
    waypoint = get_selected_waystation()
    if not waypoint:
        messagebox.showinfo("Silk Road", "Select a waystation first.")
        return
    if not messagebox.askyesno("Silk Road", f"Remove waystation from config?\n\n{waypoint['path']}"):
        return
    target = waypoint["path"].lower()
    for record in g["config"]["waypoints"]:
        if str(Path(record["path"]).expanduser().resolve()).lower() == target:
            record["enabled"] = False
    save_config(g["execroot"], g["config"])
    set_status(f"Waystation disabled: {waypoint['path']}")
    refresh_all()


def remove_selected_waypoint():
    remove_selected_waystation()


def open_selected_waystation():
    waypoint = get_selected_waystation()
    if not waypoint:
        messagebox.showinfo("Silk Road", "Select a waystation first.")
        return
    path = Path(waypoint["path"])
    if not path.exists():
        messagebox.showerror("Silk Road", f"Waystation path does not exist:\n{path}")
        return
    open_path(path)
    set_status(f"Opened waystation: {path}")


def open_selected_waypoint():
    open_selected_waystation()


def get_selected_waystation():
    tree = g["widgets"]["waystations"]
    selection = tree.selection()
    if not selection:
        return None
    values = tree.item(selection[0], "values")
    selected_path = str(Path(values[2]).expanduser().resolve()).lower()
    for waypoint in get_enabled_waypoints(g["config"]):
        if waypoint["path"].lower() == selected_path:
            return waypoint
    return None


def get_selected_waypoint():
    return get_selected_waystation()


def open_path(path):
    import os
    import platform
    import subprocess

    path = str(path)
    system = platform.system().lower()
    if system == "windows":
        os.startfile(path)
    elif system == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def edit_selected_sherpa_code():
    sherpa_name = get_selected_sherpa_name() or C.SHERPA_DOCUMENT_INDEXER
    record = g["config"]["sherpas"].get(sherpa_name)
    if not record:
        messagebox.showerror("Silk Road", f"Unknown Sherpa: {sherpa_name}")
        return
    path = Path(record["component"])
    if not path.exists():
        messagebox.showerror("Silk Road", f"Component file does not exist:\n{path}")
        return

    win = tk.Toplevel(g["root"])
    win.title(f"Edit Sherpa Code - {sherpa_name}")
    win.geometry("900x650")
    win.columnconfigure(0, weight=1)
    win.rowconfigure(1, weight=1)

    ttk.Label(win, text=str(path)).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
    text = tk.Text(win, wrap="none", undo=True)
    text.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)
    text.insert("1.0", path.read_text(encoding="utf-8"))

    buttons = ttk.Frame(win)
    buttons.grid(row=2, column=0, sticky="e", padx=10, pady=10)
    ttk.Button(buttons, text="Save", command=lambda: save_sherpa_code(path, text)).grid(row=0, column=0, padx=(0, 4))
    ttk.Button(buttons, text="Run After Save", command=lambda: save_and_run_sherpa(path, text, win, sherpa_name)).grid(row=0, column=1, padx=(0, 4))
    ttk.Button(buttons, text="Close", command=win.destroy).grid(row=0, column=2)


def show_interval_window():
    sherpa_name = get_selected_sherpa_name() or C.SHERPA_DOCUMENT_INDEXER
    record = g["config"]["sherpas"].get(sherpa_name)
    if not record:
        messagebox.showerror("Silk Road", f"Unknown Sherpa: {sherpa_name}")
        return

    win = tk.Toplevel(g["root"])
    win.title(f"Sherpa Interval - {sherpa_name}")
    win.geometry("420x170")
    win.columnconfigure(1, weight=1)

    current_seconds = int(record.get("interval_seconds", 1800))
    minutes_var = tk.StringVar(value=str(max(1, current_seconds // 60)))

    ttk.Label(win, text="Run every").grid(row=0, column=0, sticky="w", padx=10, pady=(14, 4))
    ttk.Entry(win, textvariable=minutes_var, width=10).grid(row=0, column=1, sticky="w", padx=10, pady=(14, 4))
    ttk.Label(win, text="minutes").grid(row=0, column=2, sticky="w", padx=10, pady=(14, 4))

    note = ttk.Label(win, text="The next scheduled run is recalculated when you save.")
    note.grid(row=1, column=0, columnspan=3, sticky="w", padx=10, pady=6)

    actions = ttk.Frame(win)
    actions.grid(row=2, column=0, columnspan=3, sticky="e", padx=10, pady=14)
    ttk.Button(actions, text="Save", command=lambda: save_sherpa_interval(win, sherpa_name, minutes_var)).grid(row=0, column=0, padx=(0, 4))
    ttk.Button(actions, text="Cancel", command=win.destroy).grid(row=0, column=1)


def save_sherpa_interval(win, sherpa_name, minutes_var):
    try:
        minutes = int(minutes_var.get().strip())
    except ValueError:
        messagebox.showerror("Silk Road", "Interval must be a whole number of minutes.")
        return
    if minutes < 1:
        messagebox.showerror("Silk Road", "Interval must be at least 1 minute.")
        return

    seconds = minutes * 60
    g["config"]["sherpas"][sherpa_name]["interval_seconds"] = seconds
    g["state"]["sherpas"][sherpa_name]["next_run"] = compute_next_run(g["config"], sherpa_name)
    save_config(g["execroot"], g["config"])
    save_state(g["execroot"], g["state"])
    set_status(f"{sherpa_name} interval set to {minutes} minute(s).")
    win.destroy()
    if "waystations" in g["widgets"] and "sherpas" in g["widgets"]:
        refresh_all()


def save_sherpa_code(path, text):
    path.write_text(text.get("1.0", "end-1c"), encoding="utf-8")
    set_status(f"Saved Sherpa component: {path}")


def save_and_run_sherpa(path, text, win, sherpa_name):
    save_sherpa_code(path, text)
    win.destroy()
    start_sherpa(sherpa_name, "manual")


def get_selected_sherpa_name():
    tree = g["widgets"]["sherpas"]
    selection = tree.selection()
    if not selection:
        return None
    values = tree.item(selection[0], "values")
    return values[0]


def show_logs_window():
    from .config import get_project_path

    log_path = get_project_path(g["execroot"]) / C.EVENT_LOG
    if log_path.exists():
        content = log_path.read_text(encoding="utf-8")
    else:
        content = "No log file exists yet."
    show_text_window("Sherpa Run Logs", content or "Log file is empty.")


def show_failures_window():
    from .config import get_project_path

    lines = []
    for name, record in g["state"]["sherpas"].items():
        failure = record.get("last_failure")
        if failure:
            lines.append(f"{name}: {failure}")
    for waypoint in get_enabled_waypoints(g["config"]):
        malformed_path = get_silk_cache_dir(waypoint) / "malformed.json"
        malformed = read_json(malformed_path, default=None)
        if malformed and malformed.get("files"):
            lines.append("")
            lines.append(f"Malformed documents from {waypoint['name']}:")
            for item in malformed["files"]:
                lines.append(f"- {item['path']}: {item['error']}")
    log_path = get_project_path(g["execroot"]) / C.EVENT_LOG
    lines.append("")
    lines.append(f"Event log: {log_path}")
    show_text_window("Sherpa Failures", "\n".join(lines) if lines else "No failures recorded.")


def refresh_all():
    refresh_waystations()
    refresh_sherpas()


def refresh_waystations():
    tree = g["widgets"]["waystations"]
    selected = set(tree.selection())
    tree.delete(*tree.get_children())
    for waypoint in get_enabled_waypoints(g["config"]):
        marker = read_waypoint_marker(waypoint["path"])
        iid = make_tree_iid("waystation", waypoint["path"])
        tree.insert("", "end", iid=iid, values=(
            marker.get("name") or waypoint["name"],
            "yes" if waypoint["has_marker"] else "no",
            waypoint["path"],
        ))
    restore_tree_selection(tree, selected)


def refresh_waypoints():
    refresh_waystations()


def refresh_sherpas():
    tree = g["widgets"]["sherpas"]
    selected = set(tree.selection())
    tree.delete(*tree.get_children())
    for name, record in g["state"]["sherpas"].items():
        counts = record.get("last_counts", {})
        iid = make_tree_iid("sherpa", name)
        tree.insert("", "end", iid=iid, values=(
            name,
            record.get("status"),
            record.get("last_run") or "",
            record.get("next_run") or "",
            counts.get("files_examined", 0),
            counts.get("valid_documents", 0),
            counts.get("duplicate_ids", 0),
            counts.get("conflicting_ids", 0),
            counts.get("failures", 0),
        ))
    restore_tree_selection(tree, selected)


def make_tree_iid(prefix, value):
    text = str(value).replace("\\", "/").replace(" ", "%20")
    for char in [":", "{", "}", "[", "]", "\n", "\t"]:
        text = text.replace(char, "_")
    return f"{prefix}:{text}"


def restore_tree_selection(tree, selected):
    existing = [iid for iid in selected if tree.exists(iid)]
    if existing:
        tree.selection_set(existing)
        tree.focus(existing[0])


def show_result(result):
    text = g["widgets"]["result"]
    text.delete("1.0", "end")
    counts = result.get("counts", {})
    lines = [
        "Document indexer result",
        "",
        f"Files examined: {counts.get('files_examined', 0)}",
        f"Valid documents: {counts.get('valid_documents', 0)}",
        f"Document IDs: {counts.get('document_ids', 0)}",
        f"Duplicate IDs: {counts.get('duplicate_ids', 0)}",
        f"Conflicting IDs: {counts.get('conflicting_ids', 0)}",
        f"Warnings: {counts.get('warnings', 0)}",
        f"Failures: {counts.get('failures', 0)}",
        "",
        "Outputs:",
    ]
    for path in result.get("output_paths", []):
        lines.append(f"- {path}")
    text.insert("1.0", "\n".join(lines))


def set_status(message):
    g["widgets"]["status"].configure(text=message)
