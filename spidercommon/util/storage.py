import os
from typing import List, Union

from spidercommon.constants import DEFAULT_STORAGE_PATH
from spidercommon.util.hashing import sha256


class HashedFile:
    """
        Class that stores files into a hashed directory structure that is four bytes separated.

        This is because of the way filesystems don't like having hundreds of thousands of files
        in the same directory.
    """
    def __init__(self, file_hash: str, storage_path: str=DEFAULT_STORAGE_PATH):
        self.storage_path = storage_path
        self.file_hash = file_hash

    @classmethod
    def from_data(cls, data: Union[bytes, str], storage_path: str=DEFAULT_STORAGE_PATH, save: bool=True):
        """
        Creates the hash for a file and saves it to its respective location.

        :param data: Data to save into the file.
        :param storage_path: Root folder for all the hashed files.
        :return:
        """
        file_hash = sha256(data)

        new_obj = cls(file_hash, storage_path)
        if save:
            new_obj.write(data)

        return new_obj

    @classmethod
    def from_hash(cls, file_hash: str, storage_path: str=DEFAULT_STORAGE_PATH):
        """
        Takes in a pre made hash and sets the references locally for them.

        :param file_hash: Hash of a file.
        :param storage_path: Root folder for all the hashed files.
        :return:
        """
        return cls(file_hash, storage_path)

    @property
    def splits(self) -> List[str]:
        """
        Generates two two-byte folder names for splitting.
        :return: The splits between the root folder and the file.
        """
        return [
            self.file_hash[0] + self.file_hash[1],
            self.file_hash[2] + self.file_hash[3]
        ]

    @property
    def full_folder_path(self) -> str:
        """
        :return: The absolute path to the folder containing files.
        """
        return os.path.abspath(os.path.join(self.storage_path, *self.splits))

    @property
    def full_path(self) -> str:
        """
        :return: The absolute path to the file.
        """
        return os.path.abspath(os.path.join(self.storage_path, *self.splits, self.file_hash))

    def write(self, data: Union[bytes, str]) -> None:
        """
        Writes the data to the file hash's location.
        :param data: Data to save into the file.
        """
        if isinstance(data, str):
            data = data.encode("utf8")

        # Create the folder tree if it does not already exist.
        if not os.path.exists(self.full_folder_path):
            os.makedirs(self.full_folder_path)

        with open(self.full_path, "wb") as f:
            f.write(data)

    def read(self) -> Union[Union[bytes, str], None]:
        """
        Reads the contents of the file if it exists.

        :return: File contents if existing, else None.
        """
        # Return nothing if the file/tree does not exist.
        if not os.path.exists(self.full_path):
            return None

        with open(self.full_path, "rb") as f:
            data = f.read()

            try:
                data = data.decode("utf8")
            except UnicodeDecodeError:
                pass

            return data
