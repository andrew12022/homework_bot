class NoneDocumentStatusError(Exception):
    """Неизвестный статус работы."""


class APIAnswerNot200Error(Exception):
    """Ответ сервера который не равен 200."""


class RequestError(Exception):
    """Ошибка запроса сервера."""
