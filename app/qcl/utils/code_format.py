from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from bleach import clean

formatter = HtmlFormatter(linenos=True)

def format(source_code: str) -> str:
    return highlight(clean(source_code), PythonLexer(), formatter)

