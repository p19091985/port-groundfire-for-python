# interface_net

Esta pasta centraliza a camada de integracao de jogo em rede.

Arquivos atuais:

- `config.py`: leitura das configuracoes de rede do `conf/options.ini`
- `session.py`: contrato base da sessao de rede e registro de jogadores
- `local_session.py`: implementacao padrao neutra, mantendo o jogo local funcionando
- `lan_client.py`: cliente TCP minimo para testes e futuras conexoes LAN
- `lan_protocol.py`: estruturas compartilhadas de descoberta, lobby e estado da partida
- `factory.py`: ponto unico para criar a sessao usada pelo restante do projeto
- `client_interface.py`: interface cliente para localizar e escolher servidores
- `server_browser_ui.py`: interface grafica inspirada no browser de servidores do Counter-Strike 1.6
- `server_browser_demo.py`: entrypoint para abrir a interface em uma janela separada
- `server/`: criador e painel de administracao para servidor dedicado

Com isso, o restante do codigo passa a consumir a camada em `interface_net`, e futuras implementacoes de host/client podem ser adicionadas aqui sem espalhar logica de rede pelo restante da arvore.

## Preview local

Para abrir somente a interface nova em uma janela separada:

```bash
python3 -m interface_net.server_browser_demo
python3 -m interface_net.server.demo
```

O renderer foi feito para depois ser desenhado dentro da janela principal do jogo usando `ServerBrowserUI.draw_to_interface(...)`.
