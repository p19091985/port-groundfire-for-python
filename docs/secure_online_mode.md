# Secure Online Mode

The online client/server path now uses `mpgameserver` as the secure transport layer.
This keeps the existing Groundfire match logic and interface flow, but moves the network
transport to an authenticated and encrypted UDP connection.

## Key Files

The secure server uses these default paths:

- `conf/network/server_root_private.pem`
- `conf/network/server_root_public.pem`

When the server starts, it creates the private/public key pair automatically if the files do not exist.

## Start The Server

```powershell
python -m src.groundfire.server
```

Custom key paths are also supported:

```powershell
python -m src.groundfire.server --server-private-key custom/private.pem --server-public-key custom/public.pem
```

## Connect A Client

The client must know the trusted server public key ahead of time.

```powershell
python -m src.groundfire.client --connect 127.0.0.1:27015 --server-public-key conf/network/server_root_public.pem
```

## Security Notes

- The server private key stays on the server.
- The client uses the server public key to authenticate the secure handshake.
- If the trusted public key file is missing, the client refuses the secure connection instead of silently falling back to an insecure mode.
