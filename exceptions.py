class NoneDocumentStatusError(Exception):
    """Неизвестный статус работы."""

    pass


class APIAnswerNot200Error(Exception):
    """Ответ сервера который не равен 200."""

    pass


class RequestError(Exception):
    """Ошибка запроса сервера."""

    pass


class StopProgrammNotTokensError(Exception):
    """Принудительная остановка программа."""

    pass
