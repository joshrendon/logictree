# logictree/api.py
from .pipeline import lower_sv_file_to_logic, lower_sv_text_to_logic


def lower_sv_to_logic(src: str):
    return lower_sv_text_to_logic(src)

__all__ = ["lower_sv_to_logic", "lower_sv_text_to_logic", "lower_sv_file_to_logic"]
