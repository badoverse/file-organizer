import os
import shutil
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


imgExtensions = [".png", ".jpeg", ".jpg", ".webp", ".gif"]
videoExtensions = [".mp4", ".webm"]
audioExtensions = [".mp3", ".wav"]
exeExtensions = [".exe"]

fileExtensions = imgExtensions + videoExtensions + audioExtensions + exeExtensions

FOLDER_NAMES = {
    "imgs": "imgs",
    "videos": "videos",
    "audios": "audios",
    "executables": "executables",
}


def category_for(extension):
    if extension in imgExtensions:
        return "imgs"
    if extension in videoExtensions:
        return "videos"
    if extension in audioExtensions:
        return "audios"
    if extension in exeExtensions:
        return "executables"
    return None


class OrganizerApp:
    def __init__(self, root):
        self.root = root
        root.title("Verse File Organizer")
        root.geometry("640x480")
        root.minsize(560, 420)

        default_source = str(Path.home() / "Downloads")
        default_dest = str(Path.home() / "Documents")

        self.source_var = tk.StringVar(value=default_source)
        self.dest_var = tk.StringVar(value=default_dest)

        pad = {"padx": 10, "pady": 6}

        main = ttk.Frame(root)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        
        ttk.Label(main, text="Source folder:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(main, textvariable=self.source_var).grid(
            row=0, column=1, sticky="ew", **pad
        )
        ttk.Button(main, text="Browse...", command=self.pick_source).grid(
            row=0, column=2, **pad
        )

        ttk.Label(main, text="Destination folder:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(main, textvariable=self.dest_var).grid(
            row=1, column=1, sticky="ew", **pad
        )
        ttk.Button(main, text="Browse...", command=self.pick_dest).grid(
            row=1, column=2, **pad
        )

        main.columnconfigure(1, weight=1)

        options_frame = ttk.LabelFrame(main, text="Categories to move")
        options_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=(6, 6))

        self.cat_vars = {}
        for i, cat in enumerate(FOLDER_NAMES):
            var = tk.BooleanVar(value=True)
            self.cat_vars[cat] = var
            ttk.Checkbutton(options_frame, text=cat, variable=var).grid(
                row=0, column=i, padx=10, pady=6, sticky="w"
            )

        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            main, text="Scan subfolders too (recursive)", variable=self.recursive_var
        ).grid(row=3, column=0, columnspan=3, sticky="w", padx=10)

        self.run_button = ttk.Button(main, text="Organize Files", command=self.start_organize)
        self.run_button.grid(row=4, column=0, columnspan=3, pady=10)

        self.progress = ttk.Progressbar(main, mode="indeterminate")
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", padx=10)

        ttk.Label(main, text="Log:").grid(row=6, column=0, sticky="w", padx=10, pady=(10, 0))
        log_frame = ttk.Frame(main)
        log_frame.grid(row=7, column=0, columnspan=3, sticky="nsew", padx=10, pady=(0, 10))
        main.rowconfigure(7, weight=1)

        self.log_text = tk.Text(log_frame, height=12, wrap="word", state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


    def pick_source(self):
        folder = filedialog.askdirectory(
            title="Select source folder", initialdir=self.source_var.get() or str(Path.home())
        )
        if folder:
            self.source_var.set(folder)

    def pick_dest(self):
        folder = filedialog.askdirectory(
            title="Select destination folder", initialdir=self.dest_var.get() or str(Path.home())
        )
        if folder:
            self.dest_var.set(folder)


    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")


    def start_organize(self):
        source = Path(self.source_var.get()).expanduser()
        dest = Path(self.dest_var.get()).expanduser()

        if not source.exists() or not source.is_dir():
            messagebox.showerror("Invalid source", f"Source folder does not exist:\n{source}")
            return
        if not dest.exists() or not dest.is_dir():
            messagebox.showerror(
                "Invalid destination", f"Destination folder does not exist:\n{dest}"
            )
            return

        active_categories = {cat for cat, var in self.cat_vars.items() if var.get()}
        if not active_categories:
            messagebox.showwarning("Nothing selected", "Select at least one category to move.")
            return

        self.clear_log()
        self.run_button.configure(state="disabled")
        self.progress.start(10)

        thread = threading.Thread(
            target=self.organize,
            args=(source, dest, active_categories, self.recursive_var.get()),
            daemon=True,
        )
        thread.start()

    def organize(self, source, dest, active_categories, recursive):
        try:
            extension_folder = {}
            for cat in active_categories:
                folder = dest / FOLDER_NAMES[cat]
                folder.mkdir(parents=True, exist_ok=True)
                extension_folder[cat] = folder

            self.log(f"Scanning: {source}")
            moved_count = 0

            if recursive:
                walker = os.walk(source)
            else:
                walker = [(str(source), [], [
                    p.name for p in source.iterdir() if p.is_file()
                ])]

            for root, _dirs, files in walker:
                for file in files:
                    filepath = Path(root) / file
                    extension = filepath.suffix.lower()

                    if extension not in fileExtensions:
                        continue

                    cat = category_for(extension)
                    if cat not in active_categories:
                        continue

                    destination_folder = extension_folder[cat]

                    if filepath.parent == destination_folder:
                        continue

                    try:
                        target = destination_folder / filepath.name
                        if target.exists():
                            stem, suffix = filepath.stem, filepath.suffix
                            i = 1
                            while target.exists():
                                target = destination_folder / f"{stem} ({i}){suffix}"
                                i += 1

                        self.log(f"Moving: {filepath} -> {target}")
                        shutil.move(str(filepath), str(target))
                        moved_count += 1
                    except Exception as e:
                        self.log(f"ERROR moving {filepath}: {e}")

            self.log(f"\nDone. {moved_count} file(s) moved.")
        except Exception as e:
            self.log(f"ERROR: {e}")
        finally:
            self.root.after(0, self.finish)

    def finish(self):
        self.progress.stop()
        self.run_button.configure(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    app = OrganizerApp(root)
    root.mainloop()