import click


@click.group()
def cli():
    """ IP Fabric CLI """
    pass


def main():
    try:
        cli()

    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
