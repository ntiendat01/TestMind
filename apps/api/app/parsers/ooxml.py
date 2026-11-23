"""Check the size of Office containers before parsing their XML."""

from io import BytesIO
from zipfile import BadZipFile, ZipFile


def validate_container(data: bytes, max_expanded_bytes: int) -> None:
    try:
        with ZipFile(BytesIO(data)) as archive:
            if "[Content_Types].xml" not in archive.namelist():
                raise ValueError("File is not an Office Open XML document.")
            if sum(member.file_size for member in archive.infolist()) > max_expanded_bytes:
                raise ValueError("The expanded Office file exceeds the size limit.")
    except BadZipFile as exc:
        raise ValueError("File is not a valid Office Open XML document.") from exc
