import importlib
from abc import abstractmethod, ABC
from typing import Optional, List, cast

from mailu_auth.config import config


class AuthenticationError(Exception):
    def __init__(self, message: str, delay: str):
        super(AuthenticationError, self).__init__(message)
        self.delay = delay


class AccessApi(ABC):

    #@abstractmethod
    #async def has_email(self, email: str) -> bool:
    #    """Checks if the `email`-address exists for logging in"""
    #    ...

    @abstractmethod
    async def get_quota(self, email: str) -> Optional[int]:
        """Gets the quota for the `email`"""
        ...

    async def has_domain(self, domain: str) -> bool:
        """Checks if the `domain` is supported as a target"""
        return domain in config.mail_domains

    @abstractmethod
    async def has_mailbox(self, email: str) -> str:
        """Checks if the `email` has a postbox assigned"""
        ...

    @abstractmethod
    async def email_redirect(self, email_alias: str) -> List[str]:
        """Gets the destinations for `email_alias` redirect. Must include both, postboxes and redirects."""
        ...

    @abstractmethod
    async def verify_postbox_access(self, email: str, password: str, client_ip: str):
        """Checks if the `user` with the `email` and the `password` is allowed to access the postbox.
        May throttle the `client_ip` in case of failure."""
        ...

    @abstractmethod
    async def verify_send_access(self, email: str, password: str, client_ip: str):
        """Checks if the `user` with the `email` and the `password` is allowed to send emails with that `address`.
        May throttle the `client_ip` in case of failure."""
        ...


access_api: AccessApi


async def startup():
    access_api_module = importlib.import_module(f'mailu_auth.access_api.{config.access_api}')
    if hasattr(access_api_module, 'startup'):
        await access_api_module.startup()
    global access_api
    access_api = access_api_module.get_api()


async def shutdown():
    access_api_module = importlib.import_module(f'mailu_auth.access_api.{config.access_api}')
    if hasattr(access_api_module, 'shutdown'):
        await access_api_module.shutdown()
    global access_api
    access_api = cast(AccessApi, None)

