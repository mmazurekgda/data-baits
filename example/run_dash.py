from data_baits.dash.app import create_dash_app
from .callbacks import callback_generator
from .layouts import layouts
import click


@click.command()
@click.option(
    "--port",
    default=8000,
    help="port to run the dash app on",
)
@click.option(
    "--debug",
    is_flag=True,
    help="run in debug mode",
)
def cli(
    port,
    debug,
):
    app = create_dash_app(
        layouts=layouts,
        callbacks_generator=callback_generator,
    )
    app.run_server(
        port=port,
        debug=debug,
    )


if __name__ == "__main__":
    cli()
