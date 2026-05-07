from __future__ import annotations

import hmac
import time
from dataclasses import dataclass

from starlette.requests import Request

from src.utils.config import WebConfig


SESSION_AUTHENTICATED = "authenticated"
SESSION_USERNAME = "username"
SESSION_CREATED_AT = "created_at"


@dataclass(frozen=True)
class CredentialStore:
    username: str
    password: str

    @classmethod
    def from_config(cls, config: WebConfig) -> "CredentialStore":
        return cls(username=config.username, password=config.password())

    def verify(self, username: str, password: str) -> bool:
        username_ok = hmac.compare_digest(username, self.username)
        password_ok = hmac.compare_digest(password, self.password)
        return username_ok and password_ok


def login_session(request: Request, username: str) -> None:
    request.session[SESSION_AUTHENTICATED] = True
    request.session[SESSION_USERNAME] = username
    request.session[SESSION_CREATED_AT] = time.time()


def logout_session(request: Request) -> None:
    request.session.clear()


def is_authenticated(request: Request) -> bool:
    return bool(request.session.get(SESSION_AUTHENTICATED))


def current_username(request: Request) -> str:
    return str(request.session.get(SESSION_USERNAME, ""))
