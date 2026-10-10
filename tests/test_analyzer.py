"""Run from the project folder: python3 -B -m unittest discover -s tests -v"""

import io
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from analyzer import analyze_code, analyze_folder, display_folder_results
from analyzer import export_report, read_python_file


SAMPLE_FOLDER = Path(__file__).resolve().parent.parent / "Code Complexity Analyzer Test"


class AnalyzerTests(unittest.TestCase):
    def test_sample_files(self):
        # Expected values are counted by hand, independently of the analyzer.
        # Order: lines, functions, classes, for, while, total loops, ifs, depth, score.
        expected = {
            "easy.py": (3, 1, 0, 0, 0, 0, 0, 0, 2),
            "medium.py": (8, 1, 0, 1, 0, 1, 1, 1, 5),
            "hard.py": (6, 1, 0, 2, 0, 2, 2, 4, 10),
        }
        keys = ("total_lines", "functions", "classes", "for_loops", "while_loops",
                "total_loops", "if_statements", "max_nesting_depth", "complexity_score")
        for name, values in expected.items():
            with self.subTest(file=name):
                result = analyze_code(read_python_file(SAMPLE_FOLDER / name))
                self.assertEqual(result, dict(zip(keys, values)))

    def test_class_method_and_while_loop(self):
        source = "class Counter:\n    def run(self):\n        while True:\n            if False:\n                break\n"
        result = analyze_code(source)
        self.assertEqual(result["classes"], 1)
        self.assertEqual(result["functions"], 1)
        self.assertEqual(result["while_loops"], 1)
        self.assertEqual(result["total_loops"], 1)
        self.assertEqual(result["if_statements"], 1)
        self.assertEqual(result["max_nesting_depth"], 2)
        self.assertEqual(result["complexity_score"], 9)

    def test_empty_code_and_sibling_blocks(self):
        result = analyze_code("")
        self.assertEqual(result["total_lines"], 0)
        self.assertEqual(result["complexity_score"], 1)
        result = analyze_code("if True:\n    pass\nif False:\n    pass\n")
        self.assertEqual(result["max_nesting_depth"], 1)
        self.assertEqual(result["complexity_score"], 3)

    def test_folder_recursion_and_invalid_file(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "nested").mkdir()
            (folder / "nested" / "valid.py").write_text("x = 1\n")
            (folder / "broken.py").write_text("def broken(")
            (folder / "notes.txt").write_text("not Python")
            reports, errors = analyze_folder(folder)
            self.assertEqual(list(reports), [str(Path("nested") / "valid.py")])
            self.assertEqual(list(errors), ["broken.py"])
            self.assertIn("Syntax error", errors["broken.py"])

    def test_sample_report_order_and_export(self):
        reports, errors = analyze_folder(SAMPLE_FOLDER)
        self.assertEqual(errors, {})
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            display_folder_results(SAMPLE_FOLDER, reports, errors)
        text = buffer.getvalue()
        self.assertLess(text.index("hard.py"), text.index("medium.py"))
        self.assertLess(text.index("medium.py"), text.index("easy.py"))
        self.assertIn("Most complex file(s), score 10/10:\n  hard.py", text)
        with TemporaryDirectory() as directory:
            output = Path(directory) / "report.txt"
            export_report(output, SAMPLE_FOLDER, reports, errors)
            self.assertEqual(output.read_text(encoding="utf-8"), text.lstrip())
            with self.assertRaises(ValueError):
                export_report(Path(directory) / "report.py", SAMPLE_FOLDER, reports, errors)

    def test_empty_folder_and_top_score_ties(self):
        with TemporaryDirectory() as directory:
            self.assertEqual(analyze_folder(directory), ({}, {}))
        reports = {"b.py": analyze_code("x = 1"), "a.py": analyze_code("y = 2")}
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            display_folder_results("samples", reports, {})
        self.assertIn("Most complex file(s), score 1/10:\n  a.py\n  b.py", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
