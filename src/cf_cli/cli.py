import typer
from .contest import app as contest_app

app = typer.Typer()
app.add_typer(contest_app, name="contest")