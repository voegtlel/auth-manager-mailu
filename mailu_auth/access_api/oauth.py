from typing import Optional, List, cast

import httpx

from mailu_auth.access_api import AccessApi, AuthenticationError
from mailu_auth.config import config


openid_mail_endpoint: str

httpx_client: httpx.AsyncClient


async def startup():
    global openid_mail_endpoint, httpx_client

    httpx_client = httpx.AsyncClient(auth=(config.mailu_oauth_client_id, config.mailu_oauth_client_secret))

    # Verify that the authentication server is available
    response = await httpx_client.get(f"{config.mailu_oauth_url}/.well-known/openid-configuration")
    response.raise_for_status()

    openid_mail_endpoint = f"{config.mailu_oauth_url}/mail"


async def shutdown():
    global openid_mail_endpoint, httpx_client
    await httpx_client.aclose()
    openid_mail_endpoint = cast(str, None)
    httpx_client = cast(httpx.AsyncClient, None)


class OAuthAccessApi(AccessApi):

    async def get_quota(self, email: str) -> Optional[int]:
        response = await httpx_client.get(f"{openid_mail_endpoint}/quota/{email}")
        if response.status_code == 404:
            raise AuthenticationError("User invalid", "0")
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, int):
            raise ValueError(f"Invalid response from server: {response.text}")
        return result or None

    async def has_mailbox(self, email: str) -> bool:
        response = await httpx_client.get(f"{openid_mail_endpoint}/postbox-exists/{email}")
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

    async def email_redirect(self, alias: str) -> List[str]:
        response = await httpx_client.get(f"{openid_mail_endpoint}/redirects/{alias}")
        if response.status_code == 404:
            raise AuthenticationError("User invalid", "0")
        response.raise_for_status()
        return response.json()

    async def verify_postbox_access(self, email: str, password: str, client_ip: str):
        email = email.lower()
        if '@' not in email:
            raise AuthenticationError("Missing '@' in address", "0")
        mail_name, domain = email.split('@', 1)
        if domain not in config.mail_domains:
            raise AuthenticationError("Invalid domain", "0")

        response = await httpx_client.post(
            f"{openid_mail_endpoint}/postbox/{email}",
            json={'password': password, 'client_ip': client_ip}
        )
        if response.status_code == 403:
            raise AuthenticationError('Invalid credentials', response.headers.get('X-Retry-Wait'))
        response.raise_for_status()

    async def verify_send_access(self, email: str, password: str, client_ip: str):
        email = email.lower()
        if '@' not in email:
            raise AuthenticationError("Missing '@' in address", "0")
        mail_name, domain = email.split('@', 1)
        if domain not in config.mail_domains:
            raise AuthenticationError("Invalid domain", "0")

        response = await httpx_client.post(
            f"{openid_mail_endpoint}/send/{email}",
            json={'password': password, 'client_ip': client_ip}
        )
        if response.status_code == 403:
            raise AuthenticationError('Invalid credentials', response.headers.get('X-Retry-Wait'))
        response.raise_for_status()


def get_api():
    return OAuthAccessApi()
