if __name__ == "__main__":
    from .cli import app
    app(prog_name="cf_cli", auto_envvar_prefix="CF_CLI")