import click
import pyfiglet as pf
from data_baits.defaults import LOGGER_NAME
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
    "--environments",
    required=True,
    help="Environments (clusters) to consider.",
    type=str,
    multiple=True,
)
@click.pass_context
def cli(ctx, verbosity, environments):
    setup_logger(
        verbosity,
        LOGGER_NAME,
    )
    ctx.obj = {
        "environments": list(set(environments)),
    }


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
