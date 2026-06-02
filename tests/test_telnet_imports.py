def test_telnet_server_imports():
    import plaguefire.frontends.telnet.Server  # noqa: F401


def test_client_renderer_imports():
    from plaguefire.frontends.telnet.ClientRenderer import render_client  # noqa: F401

    assert callable(render_client)


def test_renderer_exports_frame():
    from plaguefire.frontends.telnet.Renderer import frame

    assert callable(frame)
