from rag.cli import main


def test_help_with_no_command(capsys):
    assert main([]) == 0
    assert "usage" in capsys.readouterr().out


def test_unimplemented_command_fails():
    assert main(["ask", "why did my game crash?"]) == 1
