import re

import srslib
from fastapi import APIRouter, HTTPException

from mailu_auth import access_api
from mailu_auth.config import config

router = APIRouter()


@router.get(
    '/internal/postfix/domain/{domain_name:path}',
    tags=['Postfix'],
    response_model=str
)
async def mailbox_domain(domain_name: str) -> str:
    if re.match(r"^\[.*]$", domain_name):
        raise HTTPException(404)
    if not await access_api.access_api.has_domain(domain_name):
        raise HTTPException(404)
    return domain_name


@router.get(
    '/internal/postfix/mailbox/{email:path}',
    tags=['Postfix'],
    response_model=str
)
async def mailbox_map(email: str) -> str:
    if not await access_api.access_api.has_mailbox(email):
        raise HTTPException(404)
    return email


@router.get(
    '/internal/postfix/alias/{alias:path}',
    tags=['Postfix'],
    response_model=str
)
async def alias_map(alias: str) -> str:
    target_emails = await access_api.access_api.email_redirect(alias)
    if not target_emails:
        raise HTTPException(404)
    return ",".join(target_emails)


@router.get(
    '/internal/postfix/transport/{email:path}',
    tags=['Postfix'],
    response_model=str
)
async def transport(email: str) -> str:
    if email == '*' or re.match(r"(^|.*@)\[.*]$", email):
        raise HTTPException(404)

    # No relay
    raise HTTPException(404)


@router.get(
    '/internal/postfix/recipient/map/{recipient:path}',
    tags=['Postfix'],
    response_model=str
)
async def recipient_map(recipient: str) -> str:
    srs = srslib.SRS(config.srs_secret_key)
    if srslib.SRS.is_srs_address(recipient):
        try:
            return srs.reverse(recipient)
        except srslib.Error as error:
            raise HTTPException(404)
    raise HTTPException(404)


@router.get(
    '/internal/postfix/sender/map/{sender:path}',
    tags=['Postfix'],
    response_model=str
)
async def sender_map(sender: str) -> str:
    srs = srslib.SRS(config.srs_secret_key)
    domain = sender.split('@', 1)[-1]
    if not await access_api.access_api.has_domain(domain):
        raise HTTPException(404)
    return srs.forward(sender, config.domain)


@router.get(
    '/internal/postfix/sender/login/{sender:path}',
    tags=['Postfix'],
    response_model=str
)
async def sender_login(sender: str) -> str:
    target_emails = await access_api.access_api.email_redirect(sender)
    if target_emails:
        raise HTTPException(404)
    return ",".join(target_emails)


@router.get(
    '/internal/postfix/sender/access/{sender:path}',
    tags=['Postfix'],
    response_model=str
)
async def sender_access(sender: str) -> str:
    if '@' not in sender:
        raise HTTPException(404)
    domain = sender.split('@', 1)[-1]
    if not await access_api.access_api.has_domain(domain):
        raise HTTPException(404)
    return 'REJECT'
