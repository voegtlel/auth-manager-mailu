import ipaddress
import socket
import urllib.parse
from enum import Enum
from typing import Optional, Tuple

from fastapi import APIRouter, HTTPException, Header
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from mailu_auth import access_api
from mailu_auth.access_api import AuthenticationError
from mailu_auth.config import config

router = APIRouter()


class AuthMethod(Enum):
    none = "none"
    plain = "plain"
    apop = "apop"
    cram_md5 = "cram-md5"
    external = "external"


class AuthProtocol(Enum):
    imap = "imap"
    pop3 = "pop3"
    smtp = "smtp"


_default_ports = {
    AuthProtocol.imap: 143,
    AuthProtocol.pop3: 110,
    AuthProtocol.smtp: 25
}

_auth_failure_message = {
    AuthProtocol.imap: "AUTHENTICATIONFAILED",
    AuthProtocol.pop3: "-ERR Authentication failed",
    AuthProtocol.smtp: "535 5.7.8",
}


def _auth_error(auth_protocol: AuthProtocol, delay: str) -> Response:
    return Response(
        headers={
            'Auth-Status': "Authentication credentials invalid",
            'Auth-Error-Code': _auth_failure_message[auth_protocol],
            'Auth-Wait': delay,
        }
    )


def _auth_success(auth_server: str, auth_port: str) -> Response:
    return Response(
        headers={
            'Auth-Status': 'OK',
            'Auth-Server': auth_server,
            'Auth-Port': auth_port
        }
    )


@router.get(
    '/internal/nginx/auth',
    tags=['NGinx Auth'],
    response_model=None,
)
async def nginx_auth(
        auth_method: AuthMethod = Header(...),
        auth_protocol: AuthProtocol = Header(...),
        auth_user: Optional[str] = Header(None),
        auth_pass: Optional[str] = Header(None),
        auth_login_attempt: int = Header(1),
        client_ip: str = Header(...),
        client_host: str = Header(...),
) -> Response:
    """
    Authentication for nginx `auth_http`. Use like::

        auth_http http://myserver/nginx/auth;
        auth_http_pass_client_cert off;
        auth_http_timeout 60s;
    """

    if auth_login_attempt > 10:
        return Response(
            headers={'Auth-Status': 'Invalid login or password'},
        )

    client_ip = urllib.parse.unquote(client_ip)

    if auth_method == AuthMethod.none and auth_protocol == AuthProtocol.smtp:
        return _auth_success(*await get_auth_server(auth_protocol))
    elif auth_method == AuthMethod.plain:
        if auth_user is None or auth_pass is None:
            raise HTTPException(400, "Missing Auth-User or Auth-Pass")

        raw_user = urllib.parse.unquote(auth_user)
        address = raw_user.encode("iso8859-1").decode("utf8")
        raw_password = urllib.parse.unquote(auth_pass)
        password = raw_password.encode("iso8859-1").decode("utf8")

        if len(password) < 8:
            return _auth_error(auth_protocol, "0")
        if auth_protocol in (AuthProtocol.imap, AuthProtocol.pop3):
            try:
                await access_api.access_api.verify_postbox_access(address, password, client_ip)
            except AuthenticationError as e:
                return _auth_error(auth_protocol, e.delay)
        elif auth_protocol == AuthProtocol.smtp:
            try:
                await access_api.access_api.verify_send_access(address, password, client_ip)
            except AuthenticationError as e:
                return _auth_error(auth_protocol, e.delay)
        return _auth_success(*await get_auth_server(auth_protocol, True))
    raise HTTPException(400, "Invalid request")


async def get_auth_server(protocol: AuthProtocol, authenticated: bool = False) -> Tuple[str, str]:
    if protocol == AuthProtocol.imap:
        auth_server, default_port = config.imap_address, "143"
    elif protocol == AuthProtocol.pop3:
        auth_server, default_port = config.pop3_address, "110"
    elif protocol == AuthProtocol.smtp:
        if authenticated:
            auth_server, default_port = config.authsmtp_address, "10025"
        else:
            auth_server, default_port = config.smtp_address, "25"
    else:
        raise ValueError(f"Invalid protocol {protocol}")
    if ':' in auth_server:
        auth_server, auth_port = auth_server.rsplit(':')
    else:
        auth_port = default_port
    try:
        ipaddress.ip_address(auth_server)
    except ValueError:
        auth_server = await run_in_threadpool(socket.gethostbyname, auth_server)
    return auth_server, auth_port
