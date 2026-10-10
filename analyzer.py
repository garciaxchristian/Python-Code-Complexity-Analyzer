"""Analyze Python files or folders using only the standard library."""

import ast
from contextlib import redirect_stdout
import io
from pathlib import Path
import tokenize


def read_python_file(file_path):
    """Read a .py file, respecting Python's source encoding declaration."""
    path = Path(file_path).expanduser()
    if path.suffix.lower() != ".py":
        raise ValueError("Please select a file with a .py extension.")
    with tokenize.open(path) as file:
        return file.read()


def get_max_nesting_depth(node, current_depth=0):
    """Find the deepest combination of if, for, and while blocks."""
    if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While)):
        current_depth += 1

    maximum_depth = current_depth
    for child in ast.iter_child_nodes(node):
        child_depth = get_max_nesting_depth(child, current_depth)
        maximum_depth = max(maximum_depth, child_depth)
    return maximum_depth


def calculate_complexity_score(if_count, for_count, while_count, depth,
                               functions=0, classes=0):
    """Return a simple educational score, bounded between 1 and 10."""
    # Start at 1. Decisions and definitions add 1; each loop adds 2.
    score = 1 + if_count + functions + classes + 2 * (for_count + while_count)
    # Each nesting level beyond the first adds 3: nesting has the most weight.
    score += 3 * max(0, depth - 1)
    # Keep this project's custom score within the 1–10 range.
    return min(10, score)


def analyze_code(source, filename="<input>"):
    """Parse source code and return its counts, nesting depth, and score."""
    tree = ast.parse(source, filename=filename)
    results = {
        "total_lines": len(source.splitlines()),
        "functions": 0,
        "classes": 0,
        "if_statements": 0,
        "for_loops": 0,
        "while_loops": 0,
    }

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            results["functions"] += 1
        elif isinstance(node, ast.ClassDef):
            results["classes"] += 1
        elif isinstance(node, ast.If):
            results["if_statements"] += 1
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            results["for_loops"] += 1
        elif isinstance(node, ast.While):
            results["while_loops"] += 1

    results["max_nesting_depth"] = get_max_nesting_depth(tree)
    results["total_loops"] = results["for_loops"] + results["while_loops"]
    results["complexity_score"] = calculate_complexity_score(
        results["if_statements"],
        results["for_loops"],
        results["while_loops"],
        results["max_nesting_depth"],
        results["functions"],
        results["classes"],
    )
    return results


def display_results(file_path, results):
    """Print a readable report in the terminal."""
    print(f"\nCode Complexity Report: {file_path}")
    print("-" * 45)
    print(f"Total lines (including blanks/comments): {results['total_lines']}")
    print(f"Functions:                              {results['functions']}")
    print(f"Classes:                                {results['classes']}")
    print(f"If statements:                          {results['if_statements']}")
    print(f"For loops:                              {results['for_loops']}")
    print(f"While loops:                            {results['while_loops']}")
    print(f"Total loops:                            {results['total_loops']}")
    print(f"Maximum nesting depth:                  {results['max_nesting_depth']}")
    print(f"Simple complexity score:                {results['complexity_score']}/10")


def analyze_folder(folder_path):
    """Analyze every Python file recursively, collecting errors separately."""
    folder = Path(folder_path).expanduser()
    if not folder.is_dir():
        raise ValueError("Please select an existing folder.")

    reports = {}
    errors = {}
    python_files = sorted(
        path for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() == ".py"
    )
    for path in python_files:
        # Relative paths distinguish files with the same name in subfolders.
        name = str(path.relative_to(folder))
        try:
            reports[name] = analyze_code(read_python_file(path), filename=str(path))
        except SyntaxError as error:
            errors[name] = f"Syntax error on line {error.lineno}: {error.msg}"
        except (OSError, UnicodeError, ValueError, RecursionError) as error:
            errors[name] = str(error)
    return reports, errors


def get_sort_key(file_report):
    """Sort higher scores first, then file names alphabetically for ties."""
    name, result = file_report
    return (-result["complexity_score"], name)


def display_folder_results(folder_path, reports, errors):
    """Print a sorted table and identify files tied for the highest score."""
    print(f"\nFolder Complexity Report: {folder_path}")
    if reports:
        sorted_reports = sorted(reports.items(), key=get_sort_key)
        name_width = max(len("File"), max(len(name) for name in reports))
        header = (
            f"{'File':<{name_width}}  {'Lines':>5}  {'Functions':>9}  "
            f"{'Classes':>7}  {'For':>5}  {'While':>5}  {'Total loops':>11}  "
            f"{'Ifs':>5}  {'Depth':>5}  {'Score':>6}"
        )
        print(header)
        print("-" * len(header))
        for name, result in sorted_reports:
            print(
                f"{name:<{name_width}}  {result['total_lines']:>5}  "
                f"{result['functions']:>9}  {result['classes']:>7}  "
                f"{result['for_loops']:>5}  {result['while_loops']:>5}  "
                f"{result['total_loops']:>11}  {result['if_statements']:>5}  "
                f"{result['max_nesting_depth']:>5}  "
                f"{str(result['complexity_score']) + '/10':>6}"
            )

        highest_score = sorted_reports[0][1]['complexity_score']
        most_complex = [
            name for name, result in sorted_reports
            if result['complexity_score'] == highest_score
        ]
        print(f"\nMost complex file(s), score {highest_score}/10:")
        for name in most_complex:
            print(f"  {name}")
        print("Lines include blanks/comments. Loops = for + while.")
    elif errors:
        print("No Python files could be analyzed successfully.")
    else:
        print("No .py files found in this folder or its subfolders.")

    if errors:
        print("\nFiles that could not be analyzed:")
        for name, error in errors.items():
            print(f"  {name}: {error}")
    print(f"\nAnalyzed: {len(reports)} file(s). Failed: {len(errors)} file(s).")


def export_report(output_path, selected_path, reports, errors):
    """Save the same sorted report shown in the terminal as UTF-8 text."""
    output = Path(output_path).expanduser()
    if output.suffix.lower() != ".txt":
        raise ValueError("Use a .txt extension for the report.")
    # Capture the existing display function so saved and terminal reports agree.
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        display_folder_results(selected_path, reports, errors)
    output.write_text(buffer.getvalue().lstrip(), encoding="utf-8")


def main():
    """Ask for a file or folder path and display the appropriate report."""
    print("Python Code Complexity Analyzer")
    try:
        file_path = input("Enter the path to a Python .py file or a folder: ").strip()
        if not file_path:
            print("No path selected.")
            return
        # Allow a path copied with surrounding single or double quotes.
        if file_path[0] == file_path[-1] and file_path[0] in ("'", '"'):
            file_path = file_path[1:-1]
        path = Path(file_path).expanduser()
        if path.is_dir():
            reports, errors = analyze_folder(path)
            display_folder_results(path, reports, errors)
        else:
            source = read_python_file(path)
            results = analyze_code(source, filename=str(path))
            display_results(path, results)
            reports, errors = {path.name: results}, {}
        output_path = input("Save a text report? Enter a .txt path, or press Enter to skip: ").strip()
        if output_path:
            export_report(output_path, path, reports, errors)
            print(f"Report saved to {output_path}")
    except SyntaxError as error:
        print(f"Python syntax error on line {error.lineno}: {error.msg}")
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print(f"Could not analyze the selected path: {error}")
    except (EOFError, KeyboardInterrupt):
        print("\nAnalysis cancelled.")


if __name__ == "__main__":
    main()
