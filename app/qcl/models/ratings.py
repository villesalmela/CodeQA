
from qcl.models import function
from qcl.utils import dbrunner


class Rating:

    def __init__(self, function_id, user_id, value: int) -> None:
        self.function_id = function_id
        self.reviewer_id = user_id
        self.value = value
        function_data = function.get_function(function_id)
        author_id = function_data["user_id"]
        if self.reviewer_id == author_id:
            raise PermissionError("Not allowed to rate own work.")
        
    def save(self):
        query = """
            INSERT INTO ratings (function_id, user_id, value)
            VALUES (:function_id, :user_id, :value)
            ON CONFLICT (function_id, user_id)
            DO UPDATE SET value=:value;
        """
        params = {"function_id": self.function_id,
                "user_id": self.reviewer_id,
                "value": self.value}
        try:
            dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to save rating") from e
    

def calc_avg_rating(function_id) -> int:
    query = "SELECT COALESCE(ROUND(AVG(value)), 0) FROM ratings WHERE function_id=:function_id"
    params = {"function_id": function_id}
    try:
        result = dbrunner.execute(query, params)
    except Exception as e:
        raise RuntimeError("Failed to calculate average rating") from e
    row = result.first()
    return row[0]

def get_rating(function_id, user_id) -> int:
    query = "SELECT COALESCE(SUM(value), 0) FROM ratings WHERE user_id=:user_id AND function_id=:function_id"
    params = {"function_id": function_id,
              "user_id": user_id}
    try:
        result = dbrunner.execute(query, params)
    except Exception as e:
        raise RuntimeError("Failed to read rating") from e
    row = result.first()
    return row[0]
