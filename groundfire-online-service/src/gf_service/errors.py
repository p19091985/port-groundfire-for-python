from __future__ import annotations


class ServiceError(Exception):
    def __init__(self, status: int, code: str, message: str, *, retryable: bool = False, details: dict | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}


def bad_request(code: str, message: str, **details: object) -> ServiceError:
    return ServiceError(400, code, message, details=details)


def forbidden(code: str = "forbidden", message: str = "Operação não permitida.") -> ServiceError:
    return ServiceError(403, code, message)


def conflict(code: str, message: str, *, retryable: bool = False, **details: object) -> ServiceError:
    return ServiceError(409, code, message, retryable=retryable, details=details)


def not_found() -> ServiceError:
    return ServiceError(404, "not_found", "Recurso não encontrado.")
