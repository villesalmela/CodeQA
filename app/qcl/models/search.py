from qcl.utils import dbrunner
import json

class SearchResult:
    def __init__(self, result_type: str, function_id: int, function_name: str, context: str, match: str) -> None:
        self.result_type = result_type
        self.function_id = function_id
        self.function_name = function_name
        self.context = context
        self.match = match

    def __str__(self) -> str:
        return json.dumps(
            {"result_type": self.result_type,
             "function_id": self.function_id,
             "function_name": self.function_name,
             "context": self.context,
             "match": self.match}
        )

def search_keywords(arg: str) -> list[SearchResult]:
    
    query = "SELECT function_id, name, keywords FROM functions WHERE keywords ILIKE :arg"
    target_field = "keywords"
    return _search(arg, query, target_field)

def search_usecase(arg: str) -> list[SearchResult]:
    query = "SELECT function_id, name, usecase FROM functions WHERE usecase ILIKE :arg"
    target_field = "usecase"
    return _search(arg, query, target_field)

def search_code(arg: str) -> list[SearchResult]:
    query = "SELECT function_id, name, code FROM functions WHERE code ILIKE :arg"
    target_field = "code"
    funcs = _search(arg, query, target_field)
    out = []
    for func in funcs:
        lines = func.context.splitlines()
        for line in lines:
            if arg in line:
                out.append(SearchResult(result_type="source code", function_id=func.function_id,
                                        function_name=func.function_name, context=line, match=arg))
                
    return out

def _search(arg: str, query: str, target_field: str) -> list[SearchResult]:
    out = []

    # take copy of the search query before altering it
    arg_orig = arg

    # sanitize the argument by escaping user-added wildcards
    arg = arg.replace("%", "\\%").replace("_", "\\_")
    
    # add wildcards
    arg = f"%{arg}%"

    params = {"arg": arg}
    result = dbrunner.execute(query, params)
    rows = result.all()
    for row in rows:
        out.append(SearchResult(result_type=target_field, function_id=row.function_id,
                                function_name=row.name, context=getattr(row, target_field), match=arg_orig))
    return out