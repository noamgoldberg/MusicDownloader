from typing import Union, List, Dict, Any

from core.display.song import SongDisplay
from core.display.playlist import PlaylistDisplay


class Display:
    
    DISPLAY_CLASSES = {
        "song": SongDisplay,
        "playlist": PlaylistDisplay, 
    }
    
    def __init__(self, entity_object: Any):
        entity_type = getattr(entity_object, "ENTITY_TYPE", None)
        display_class = self.DISPLAY_CLASSES.get(entity_type)
        if display_class is None:
            raise ValueError(f"Invalid entity_type '{entity_type}'.")
        self.display_object = display_class(entity_object)
    
    def display(self) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Displays the entity."""
        return self.display_object.display()