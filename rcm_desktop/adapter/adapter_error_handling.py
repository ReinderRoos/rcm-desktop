"""Minimale exception-keten voor adapter-foutpaden (slice 90)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rcm_desktop.adapter.validate_service import UserFacingError


def log_adapter_exception(logger_name: str, exc: BaseException, *, context: str) -> None:
    logging.getLogger(logger_name).exception("%s", context, exc_info=exc)


def user_facing_from_exception(
    logger_name: str,
    *,
    code: str,
    message: str,
    exc: BaseException,
    context: str,
) -> UserFacingError:
    from rcm_desktop.adapter.validate_service import UserFacingError

    log_adapter_exception(logger_name, exc, context=context)
    err = UserFacingError(code=code, message=message)
    err.__cause__ = exc
    return err
