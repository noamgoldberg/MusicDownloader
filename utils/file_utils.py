from typing import Optional

def format_safe_filename(
    filename: str,
    suffix: Optional[str] = None
) -> str:
    filename = filename \
        .replace(' /', ' -').replace('/ ', '- ').replace('/', '-') \
        .replace(' \\', ' -').replace('\\ ', '- ').replace('\\', '-')
    if suffix:
        filename += suffix
    return filename