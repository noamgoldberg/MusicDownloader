from typing import List, Optional, Union, Generator, Dict
from io import BytesIO
import zipfile
from stqdm import stqdm as st_tqdm
from pathlib import Path



def zip_audio_files(
    songs: Union[List, Generator, Dict[str, BytesIO]],
    stqdm: bool = False,
    batch_size: Optional[int] = None,
    total: Optional[int] = None,
) -> Union[BytesIO, List[BytesIO]]:
    """
    Zip the audio files of songs or videos and return the zip as a binary object.
    
    Parameters:
    - songs: A list of songs or videos to be zipped.
    - stqdm: Whether to use the streamlit tqdm progress bar.
    - desc: Description for the progress bar.
    - batch_size: The number of items to include in each zip file. If None, all items are zipped into a single file.

    Returns:
    - If batch_size is None, returns a single zip file as a BytesIO object.
    - If batch_size is set, returns a list of BytesIO objects, each representing a zipped batch of songs.
    """
    if batch_size is None:
        # If no batch size is provided, zip everything into one file.
        return _zip_audio_batch(songs, stqdm=stqdm, total=total)
    
    # Otherwise, split the songs into batches and zip each batch.
    if isinstance(songs, dict):
        raise NotImplementedError("Songs of type 'dict' (already zipped audio with titles as keys) not yet implemented for batch_size != None")
    zipped_files = []
    batch = []
    for i, song in enumerate(songs):
        batch.append(song)
        # Once the batch reaches the desired size, process it
        if len(batch) == batch_size:
            batch_buffer = _zip_audio_batch(batch, stqdm=stqdm, total=len(batch))
            zipped_files.append(batch_buffer)
            batch = []  # Reset batch for the next one

    # Handle the remaining songs if any after the loop
    if batch:
        batch_buffer = _zip_audio_batch(batch, stqdm=stqdm, total=len(batch))
        zipped_files.append(batch_buffer)
    
    return zipped_files

def _zip_audio_batch(
    songs: Union[List, Generator, Dict[str, BytesIO]],
    stqdm: bool = False,
    total: Optional[int] = None,
) -> BytesIO:
    """Helper function to zip a single batch of songs."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as audio_zip:
        items = st_tqdm(songs) if stqdm else songs
        for i, item in enumerate(items):
            if isinstance(songs, dict):
                if stqdm:
                    items.set_description(f"{i + 1} / {len(songs)} Zipping Zipped Files: {Path(item).stem}")
                data = songs[item]
                safe_filename = f"{item}".replace(' ', '_').replace('/', '_').replace('\\', '_')
            else:
                if stqdm:
                    actions_str = "Downloading & Zipping" if not item._audio else "Zipping"
                    items.set_description(f"{i + 1} / {total} {actions_str}: {item.title}")
                item.download_audio()
                data = item._audio
                safe_filename = f"{item.filename}".replace(' ', '_').replace('/', '_').replace('\\', '_')
            try:
                audio_zip.writestr(safe_filename, data.getvalue())
            except AttributeError:
                print("breakpoint")
    buf.seek(0)
    return buf
