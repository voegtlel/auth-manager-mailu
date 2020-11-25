<a href="https://cloud.docker.com/repository/docker/voegtlel/auth-manager-backend/builds">
  <img src="https://img.shields.io/docker/cloud/build/voegtlel/auth-manager-backend.svg" alt="Docker build status" />
</a>
<img src="https://img.shields.io/github/license/voegtlel/auth-manager-backend.svg" alt="License" />

# Alternative authentication backend for mailu for the auth-manager ecosystem

This is an alternative backend for the [mailu](https://github.com/Mailu/Mailu) email server leveraging the [auth-manager](https://github.com/voegtlel/auth-manager-frontend) ecosystem.

## Deployment server

Use an AGSI server and import `mailu_auth.app:app`.

# Config

## Required environment variables
```
BACKEND_CORS_ORIGIN=["http://127.0.0.1:4200"]
MAILU_AUTH_API_AUTH_TOKEN=123456
MAILU_AUTH_API_URL=http://localhost:5000
ALLOW_NETS=0.0.0.0/0
IMAP_ADDRESS=localhost
POP3_ADDRESS=localhost
AUTHSMTP_ADDRESS=localhost
SMTP_ADDRESS=localhost
```

## Docker compose

```
version: '3'
services:
  front:
    image: ${DOCKER_ORG:-mailu}/${DOCKER_PREFIX:-}nginx:${MAILU_VERSION:-1.7}
    restart: always
    env_file: mailu.env
    logging:
      driver: json-file
    ports:
      - "127.0.0.1:80:80"
      - "::1:80:80"
      - "127.0.0.1:443:443"
      - "::1:443:443"
      - "127.0.0.1:25:25"
      - "::1:25:25"
      - "127.0.0.1:465:465"
      - "::1:465:465"
      - "127.0.0.1:587:587"
      - "::1:587:587"
      - "127.0.0.1:110:110"
      - "::1:110:110"
      - "127.0.0.1:995:995"
      - "::1:995:995"
      - "127.0.0.1:143:143"
      - "::1:143:143"
      - "127.0.0.1:993:993"
      - "::1:993:993"
    volumes:
      - "/mailu/certs:/certs"
      - "/mailu/overrides/nginx:/overrides"

  imap:
    image: ${DOCKER_ORG:-mailu}/${DOCKER_PREFIX:-}dovecot:${MAILU_VERSION:-1.7}
    restart: always
    env_file: mailu.env
    volumes:
      - "/mailu/mail:/mail"
      - "/mailu/overrides:/overrides"
    depends_on:
      - front

  smtp:
    image: ${DOCKER_ORG:-mailu}/${DOCKER_PREFIX:-}postfix:${MAILU_VERSION:-1.7}
    restart: always
    env_file: mailu.env
    volumes:
      - "/mailu/overrides:/overrides"
    depends_on:
      - front

  antispam:
    image: ${DOCKER_ORG:-mailu}/${DOCKER_PREFIX:-}rspamd:${MAILU_VERSION:-1.7}
    restart: always
    env_file: mailu.env
    volumes:
      - "/mailu/filter:/var/lib/rspamd"
      - "/mailu/dkim:/dkim"
      - "/mailu/overrides/rspamd:/etc/rspamd/override.d"
    depends_on:
      - front

  admin:
    image: voegtlel/auth-manager-backend
    restart: unless-stopped
    volumes:
      - ./key.private:/app/key.private
    environment:
      MAIL_DOMAINS=["localhost.localdomain"]

      MAILU_OAUTH_URL: https://auth.example.com
      MAILU_OAUTH_CLIENT_ID: mail 
      MAILU_OAUTH_CLIENT_SECRET: 123456
      ALLOW_NETS: 192.168.1.0/24  # Put the docker network here
      MAIL_DOMAINS: '["example.com"]'  # Put the domain of allowed mail addresses here (xyz@example.com)
```

# License

MIT
