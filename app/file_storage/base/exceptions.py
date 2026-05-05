class FileStorageError(Exception):
    """
    Базовое исключение для операций с хранилищем.
    """

    pass


class StorageFileNotFoundError(FileStorageError):
    """
    Файл не найден в хранилище.
    """

    pass
