from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from mailu_auth.config import config
from mailu_auth.dovecot import router as dovecot_router
from mailu_auth.postfix import router as postfix_router
from mailu_auth.nginx_auth import router as nginx_auth_router

app = FastAPI()

app.include_router(dovecot_router)
app.include_router(postfix_router)
app.include_router(nginx_auth_router)


@app.on_event('startup')
async def startup():
    import mailu_auth.access_api
    await mailu_auth.access_api.startup()


@app.on_event('shutdown')
async def shutdown():
    import mailu_auth.access_api
    await mailu_auth.access_api.shutdown()
