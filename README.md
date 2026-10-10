# Python Code Complexity Analyzer

This project checks a Python file or a whole folder and shows basic code metrics. It uses Python's built-in `ast` module to inspect code without running it and `pathlib` to find files. You can use the terminal version or the Tkinter GUI. Both use the same analysis code and Python's standard library.

## Run the GUI

From the project folder, run:

```sh
python3 -B gui.py
```

Click **Select File** or **Select Folder**. The chosen path appears above the table. Click **Analyze** to analyze it and show the results. You can click **Analyze** again after editing your files. The table shows all metrics, sorted by score from highest to lowest. The summary below the table shows the most complex file, including ties. Scroll horizontally if all columns do not fit.

Click **Export Report** to save the results as a `.txt` file. Files with errors are skipped and shown in a popup; their errors are also included in the saved report. Selecting a new path clears the old results. An invalid single file shows an error popup, and you can try another file.

The GUI requires Tkinter in your Python installation. Analysis runs in the window's main thread, so large folders may make the window pause until analysis finishes.

## How to run

Open a terminal in the project folder and run:

```sh
python3 -B analyzer.py
```

Enter a Python file path or a folder path. Enter `.` for the current folder, or `Code Complexity Analyzer Test` to check the easy, medium, and hard samples. All Python files in subfolders are included, even files in hidden folders or virtual environments.

After the results appear, enter a `.txt` file path, such as `report.txt`, to save a report, or press Enter to skip. The destination folder must already exist. Enter the save path without surrounding quotes. Saving replaces an existing report at that path. Reports use the folder table format, even when you analyze a single file.

Relative paths start from your terminal's current folder, and `~` expands to your home folder. The input file or folder path can have surrounding quotes. The `-B` option prevents Python from creating `__pycache__` files.

## What it measures

- File name (including its subfolder path)
- Total lines, including comments and blank lines
- Functions and classes
- For loops, while loops, and total loops
- If statements
- Maximum nesting depth
- Custom complexity score from 1 to 10

Methods and async functions count as functions. Async for loops count as for loops. Nesting measures how many if statements and loops are inside each other. An if inside a for loop has depth 2. Classes and function definitions do not add nesting levels. Python represents `elif` as another if node, so it adds to both the if count and nesting depth. Comprehensions, lambdas, and inline conditional expressions are not counted. Blocks such as `try`, `with`, and `match` do not add nesting depth.

Folder results are sorted from the highest score to the lowest. File names break ties alphabetically. The report identifies all files tied for the highest score. In folder mode, files that cannot be read or parsed are listed separately, and the other files are still analyzed. The report includes successful and failed file counts. An empty folder gets a message saying no Python files were found. In single-file mode, an invalid file gets an error message and the program ends.

## Complexity score

```text
score = 1 + functions + classes + if_statements
        + 2 * total_loops
        + 3 * max(0, nesting_depth - 1)
```

The score starts at 1. Each function, class, or if statement adds 1. Each loop adds 2. Each nesting level after the first adds 3 because deeply nested code can be harder to follow. The final score is `min(10, score)`. An empty file scores 1. Line count does not affect the score.

This is a simple custom formula, not a standard cyclomatic complexity measurement. More functions can also mean better organization, and a high score does not automatically mean bad code. Different files can share a score of 10 because of the cap.

## Automated tests

Run this command from the project folder (the folder containing `analyzer.py`):

```sh
python3 -B -m unittest discover -s tests -v
```

Use this command instead of running `tests/test_analyzer.py` directly so Python can find `analyzer.py`.

The tests use Python's built-in `unittest` module. They check hand-counted results for `easy.py`, `medium.py`, and `hard.py`, plus classes, while loops, empty input, nesting, folder searching, invalid files, sorting, ties, and report export.

## Example output

```text
Folder Complexity Report: Code Complexity Analyzer Test
File       Lines  Functions  Classes    For  While  Total loops    Ifs  Depth   Score
-------------------------------------------------------------------------------------
hard.py        6          1        0      2      0            2      2      4   10/10
medium.py      8          1        0      1      0            1      1      1    5/10
easy.py        3          1        0      0      0            0      0      0    2/10

Most complex file(s), score 10/10:
  hard.py
Lines include blanks/comments. Loops = for + while.

Analyzed: 3 file(s). Failed: 0 file(s).
```

`sample_report.txt` contains the exported report for these three files.

## Code organization

`read_python_file()` reads the source. `analyze_code()` counts its structures, and `get_max_nesting_depth()` checks nesting recursively. `calculate_complexity_score()` applies the formula. `analyze_folder()` finds and analyzes Python files. The display functions print results, and `export_report()` saves the folder-style report as text. `main()` handles terminal input.

`gui.py` builds the window using `tkinter` and `ttk`. It imports the analysis, sorting, and export functions from `analyzer.py`, so both versions use the same metrics and scores.
