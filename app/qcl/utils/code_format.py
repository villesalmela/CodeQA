from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter


def format(source_code: str) -> str:
    formatter = HtmlFormatter(linenos=True)
    return highlight(source_code, PythonLexer(), formatter)


