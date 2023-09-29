from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

formatter = HtmlFormatter(linenos=True)

def format(source_code: str) -> str:
    return highlight(source_code, PythonLexer(), formatter)


