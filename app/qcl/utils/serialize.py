from typing import Any
import json
import lzma

def compress(input_dict: dict[str, Any]) -> bytes:
    """
    Dump dictionary to a JSON string, compress it using lzma
    Returns compressed bytes
    """

    json_str = json.dumps(input_dict)
    json_bytes = json_str.encode("utf-8")
    compressed_bytes = lzma.compress(json_bytes)
    
    return compressed_bytes

def decompress(compressed_bytes: bytes) -> dict[str, Any]:
    """
    Decompress bytes using lzma, load the JSON string into dictionary
    Return dictionary
    """

    decompressed_bytes = lzma.decompress(compressed_bytes)
    json_str = decompressed_bytes.decode("utf-8")
    output_dict = json.loads(json_str)
    
    return output_dict

