import os
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import FileResponse

from mailu_auth import access_api
from mailu_auth.access_api import AuthenticationError
from mailu_auth.config import config

router = APIRouter()


class PassdbDict(BaseModel):
    password: Optional[str]
    nopassword: Optional[Literal['Y']]
    allow_nets: str
    # Changes the username (can also be done by the passdb lookup)
    user: Optional[str]


@router.get(
    '/internal/dovecot/passdb/{user_email:path}',
    tags=['Dovecot'],
    response_model=PassdbDict
)
async def passdb_dict(user_email: str):
    # TODO: Maybe this works? Simply always authenticate the user?
    # It should be checked afterwards by nginx if the user is actually permitted.
    #if not await access_api.access_api.has_email(user_email):
    #    raise HTTPException(404)
    return PassdbDict(
        password=None, nopassword='Y', allow_nets=config.allow_nets, user=user_email.lower()
    )


class UserdbDict(BaseModel):
    quota_rule: Optional[str]
    # Changes the username (can also be done by the passdb lookup)
    # user: Optional[str]


@router.get(
    '/internal/dovecot/userdb/{user_email:path}',
    tags=['Dovecot'],
    response_model=UserdbDict
)
async def userdb_dict(user_email: str):
    try:
        quota = await access_api.access_api.get_quota(user_email)
    except AuthenticationError as e:
        raise HTTPException(404, str(e))
    if quota is not None:
        return UserdbDict(quota_rule=f"*:bytes={quota}")
    return UserdbDict()


@router.post(
    '/internal/dovecot/quota/{ns}/{user_email:path}',
    tags=['Dovecot'],
)
async def save_dict(ns: str, user_email: str, request: Request):
    if ns == 'storage':
        user_used_quota = request.json()
        print(f"Update user data usage for {user_email}: {user_used_quota}")
        # No saving needed...
    return Response(status_code=200)


@router.get(
    "/internal/dovecot/sieve/data/default/{user_email:path}",
    tags=['Dovecot'],
)
async def sieve_data(user_email: str):
    return FileResponse(os.path.join(os.path.dirname(__file__), 'templates', 'default.sieve'))


@router.get(
    "/internal/dovecot/sieve/name/{script}/{user_email:path}",
    tags=['Dovecot'],
    response_model=str,
)
async def sieve_name(script: str, user_email: str):
    return script
