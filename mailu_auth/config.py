from typing import List, Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    mailu_oauth_url: Optional[str] = 'http://localhost:8000'
    mailu_oauth_client_id: Optional[str] = 'mail'
    mailu_oauth_client_secret: Optional[str]

    mail_domains: List[str]

    # Comma-separated list of networks (e.g. 192.168.0.0/16) which are allowed to use dovecot
    # without authentication (i.e. this must be the smallest net nginx is located)
    allow_nets: str

    backend_cors_origin: List[str]

    imap_address: str = "imap"
    pop3_address: str = "imap"
    authsmtp_address: str = "smtp"
    smtp_address: str = "smtp"

    access_api: str = 'oauth'


config = Settings()
