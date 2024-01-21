import click
import pyfiglet as pf
from data_baits.core.settings import settings, Environments
from data_baits.logger import setup_logger
from data_baits.generate import generate
from data_baits.deploy import deploy


@click.group()
@click.option(
    "--verbosity",
    default="INFO",
    help="verbosity of the logger",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
)
@click.option(
    "--environment",
    help="force environment of the application",
    default=None,
    type=click.Choice(Environments),
)
def cli(verbosity, environment):
    setup_logger(
        verbosity,
        settings.LOGGER_NAME,
    )
    if environment:
        settings.ENVIRONMENT = environment


cli.add_command(generate)
cli.add_command(deploy)
if __name__ == "__main__":
    click.secho(
        pf.figlet_format("Data Baits"),
        fg="blue",
        bg=None,
        bold=True,
    )
    cli()
