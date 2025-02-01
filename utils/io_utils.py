from typing import Union
from io import BytesIO


UNITS_MAP = {
    "b": 1,
    "kb": 1024,
    "mb": 1024**2,
    "gb": 1024**3,
}

def get_size(
    buffer: Union[bytes, BytesIO, None],
    units: str = "b"
) -> float:
    if buffer is None:
        return 0
    elif isinstance(buffer, bytes):
        buffer = BytesIO(buffer)
    size_in_bytes = buffer.getbuffer().nbytes

    if units.lower() not in UNITS_MAP:
        raise ValueError("Invalid unit. Use 'b', 'kb', 'mb', or 'gb'.")
    return size_in_bytes / UNITS_MAP[units.lower()]