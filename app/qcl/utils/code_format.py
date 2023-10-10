from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
import ast


def format(source_code: str) -> str:
    formatter = HtmlFormatter(linenos=True)
    return highlight(source_code, PythonLexer(), formatter)


def check_function_only(source_code: str) -> None:
    """Parse given source code and confirm it constains at least one function.
    Besides the function, only imports are allowed, other content will raise syntax error."""
    
    parsed = ast.parse(source_code)
    
    # check we can find at least one function
    has_function = any(isinstance(node, ast.FunctionDef) for node in ast.walk(parsed))
    if not has_function:
        raise SyntaxError("No function found")

    # check there is nothing but functions and imports
    for node in parsed.body:
        if not isinstance(node, (ast.FunctionDef, ast.Import, ast.ImportFrom)):
            raise SyntaxError(f"Unexpected statement {type(node).__name__}")


def check_unittest(source_code: str) -> None:
    """Parse given source code and confirm it contains one class called Test and imports unittest.
    Besides the class, only imports are allowed, other content will raise syntax error."""

    parsed = ast.parse(source_code)

    # find all imports (on main level)
    imports = set()
    for node in parsed.body:
        if isinstance(node, ast.Import):
            for item in node.names:
                imports.add(item.name)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module)
    
    # check that unittest was imported
    if "unittest" not in imports:
        raise SyntaxError("unittest not imported")

    # find all classes (on main level)
    classes = [node.name for node in parsed.body if isinstance(node, ast.ClassDef)]
    
    # check there is the needed class and nothing more
    if "Test" not in classes or len(classes) != 1:
        raise SyntaxError("Exactly one class named \"Test\" should be present")

    # check there is nothing but classes and imports
    for node in parsed.body:
        if not isinstance(node, (ast.ClassDef, ast.Import, ast.ImportFrom)):
            raise SyntaxError(f"Unexpected statement {type(node).__name__} at line {node.lineno}")

    