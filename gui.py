"""A Tkinter interface for the analysis functions in analyzer.py."""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from analyzer import analyze_code, analyze_folder, export_report
from analyzer import get_sort_key, read_python_file


class AnalyzerGUI:
    def __init__(self, root):
        self.root = root
        root.title("Python Code Complexity Analyzer")
        root.geometry("1150x550")
        root.minsize(750, 400)

        # Keep the last completed analysis for exporting.
        self.selected_path = None
        self.report_path = None
        self.reports = {}
        self.errors = {}
        self.path_text = tk.StringVar(value="Select a Python file or folder to begin.")
        self.summary = tk.StringVar(value="No results yet.")

        frame = ttk.Frame(root, padding=15)
        frame.pack(fill="both", expand=True)
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Select File", command=self.select_file).pack(side="left")
        ttk.Button(toolbar, text="Select Folder", command=self.select_folder).pack(side="left", padx=8)
        ttk.Button(toolbar, text="Analyze", command=self.analyze).pack(side="left")
        self.export_button = ttk.Button(
            toolbar, text="Export Report", command=self.save_report, state="disabled"
        )
        self.export_button.pack(side="right")
        ttk.Label(frame, textvariable=self.path_text, wraplength=1000).pack(anchor="w", pady=12)

        # Treeview is ttk's table widget. Scrollbars keep every column accessible.
        columns = (
            ("file", "File name"), ("total_lines", "Lines"),
            ("functions", "Functions"), ("classes", "Classes"),
            ("for_loops", "For loops"), ("while_loops", "While loops"),
            ("total_loops", "Total loops"), ("if_statements", "If statements"),
            ("max_nesting_depth", "Nesting depth"), ("complexity_score", "Score /10"),
        )
        self.metric_keys = [key for key, label in columns if key != "file"]
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill="both", expand=True)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.table = ttk.Treeview(
            table_frame, columns=[key for key, label in columns], show="headings"
        )
        for key, label in columns:
            self.table.heading(key, text=label)
            self.table.column(key, width=250 if key == "file" else 95,
                              minwidth=80, anchor="w" if key == "file" else "center")
        vertical = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        horizontal = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        ttk.Label(frame, textvariable=self.summary, wraplength=1000).pack(anchor="w", pady=12)
        ttk.Label(frame, text="Lines include blanks and comments. Scores use the project's custom formula.").pack(anchor="w")

    def select_file(self):
        path = filedialog.askopenfilename(
            parent=self.root, title="Select a Python file", filetypes=[("Python files", "*.py")]
        )
        if path:
            self.set_selection(path)

    def select_folder(self):
        path = filedialog.askdirectory(parent=self.root, title="Select a folder", mustexist=True)
        if path:
            self.set_selection(path)

    def set_selection(self, path):
        # Clear old results so they cannot be exported for a new selection.
        self.selected_path = Path(path)
        self.path_text.set(str(self.selected_path))
        self.clear_results()
        self.summary.set("File or folder selected. Click Analyze to show results.")

    def clear_results(self):
        for item in self.table.get_children():
            self.table.delete(item)
        self.reports = {}
        self.errors = {}
        self.report_path = None
        self.export_button.configure(state="disabled")

    def analyze(self):
        if self.selected_path is None:
            messagebox.showerror("Select a path", "Please select a Python file or folder first.", parent=self.root)
            return
        self.clear_results()
        try:
            # All parsing and scoring stay in analyzer.py.
            path = self.selected_path
            if path.is_dir():
                reports, errors = analyze_folder(path)
            else:
                result = analyze_code(read_python_file(path), filename=str(path))
                reports, errors = {path.name: result}, {}
        except (OSError, UnicodeError, ValueError, SyntaxError, RecursionError) as error:
            self.summary.set("Analysis failed. Check the selected path.")
            messagebox.showerror("Analysis error", str(error), parent=self.root)
            return

        self.reports, self.errors = reports, errors
        self.report_path = path
        sorted_reports = sorted(reports.items(), key=get_sort_key)
        for name, result in sorted_reports:
            self.table.insert("", "end", values=[name] + [result[key] for key in self.metric_keys])
        # Keep new results visible even after scrolling a previous report.
        self.table.xview_moveto(0)
        self.table.yview_moveto(0)
        rows = self.table.get_children()
        if rows:
            self.table.selection_set(rows[0])
            self.table.focus(rows[0])
            self.table.see(rows[0])
        if sorted_reports:
            highest = sorted_reports[0][1]["complexity_score"]
            names = [name for name, result in sorted_reports if result["complexity_score"] == highest]
            self.summary.set(
                f"Most complex ({highest}/10): {', '.join(names)}\n"
                f"Analyzed: {len(reports)} file(s). Failed: {len(errors)} file(s)."
            )
        else:
            self.summary.set("No Python files could be analyzed." if errors else "No .py files found.")
        # Even an empty or failed folder report can be saved.
        self.export_button.configure(state="normal")
        if errors:
            details = "\n".join(f"{name}: {error}" for name, error in errors.items())
            messagebox.showwarning("Skipped files", details, parent=self.root)

    def save_report(self):
        if self.report_path is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Export report", defaultextension=".txt",
            initialfile="report.txt", filetypes=[("Text reports", "*.txt")]
        )
        if not path:
            return
        try:
            export_report(path, self.report_path, self.reports, self.errors)
        except (OSError, UnicodeError, ValueError) as error:
            messagebox.showerror("Export error", str(error), parent=self.root)
            return
        messagebox.showinfo("Report saved", f"Saved to {path}", parent=self.root)


def main():
    root = tk.Tk()
    AnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
