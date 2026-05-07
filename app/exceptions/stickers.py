class StickerServiceError(Exception):
    pass

class TotalTaskLimit(StickerServiceError):
    """Слишком много активных задач в работе"""
    pass

class UserTaskLimitError(StickerServiceError):
    """Слишком много запросов от польщователя"""
    pass
