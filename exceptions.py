class NoTokenException(Exception):
    """Исключение, связанное с отсутствие токена в файле .env."""

    pass


class NoResponceException(Exception):
    """Исключение, связанное с недоступностью эндпоинта."""

    pass


class MessageException(Exception):
    """Исключение, связанное сошибками при отправке сообщения ботом."""

    pass


class StatusError(Exception):
    """Неверный статус работы в ответе API"""


class EndpointStatusError(Exception):
    """Возникла проблема с удаленным сервером."""


class EndpointNotAnswer(Exception):
    """Удаленный сервер не отвечает"""
