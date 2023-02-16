class NoTokenException(Exception):
    """Исключение, связанное с отсутствие токена в файле .env."""

    pass


class NoResponceException(Exception):
    """Исключение, связанное с недоступностью эндпоинта."""

    pass


class MessageException(Exception):
    """Исключение, связанное сошибками при отправке сообщения ботом."""

    pass
