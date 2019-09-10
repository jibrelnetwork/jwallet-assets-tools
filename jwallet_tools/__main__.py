#!/usr/bin/env python
import os
import sys
import logging.config
import json
import click

from .assets_validator import create_assets_validator
from .validation_service.classes import KafkaAssetValidator


sys.path.insert(0, os.path.dirname(__name__))


logger = logging.getLogger('jwallet_tools')


INDEX_FILENAME = './assets_index.json'


@click.group()
def main():
    pass


@main.command()
@click.argument('file', type=click.File('r'), required=False)
@click.option('--node', default="https://main-node.jwallet.network/", help="Ethereum node to use to validate contract")  # noqa
@click.option('--ignore', help="comma separated list of ignored methods (ex: `approve,name`)")
@click.option('--fast', is_flag=True, help="do not invoke contract method")
@click.option('--loglevel', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), default='INFO')  # noqa
@click.option('--progress', is_flag=True, default=False, help="Show progressbar")
def validate(file, node, ignore, fast, loglevel, progress):
    """
    Validate json file with assets.

    Will look at `assets_index.json` to get network list and related nodes to perform validation
    over.

    Use `--node` to define ethereum node to use to check contracts if you want to validate single
    file (also you must provide `file` argument).

    You can use `--ignore` to ignore some methods. If such methods doesn't exist,
    validation will not fail and warning will be printed to output. For example:
    `--ignore approve,name,decimals`. It is also possible to ignore all method
    by symbol with, for ex `GNT.*` or exact method with `GNT.approve`.

    Ignored methods can be also defined in `jwallet_tools/assets.schema.json` under
    `item.isValidContract.ignore` key.

    Use `--fast` to prevent method invocations.
    """
    _configure_logging(loglevel)

    check_list = []
    if node and file:
        check_list.append([file, node])
    else:
        if not os.path.exists(INDEX_FILENAME):
            click.echo('[FAIL] no %s found in current directory, '
                       'and no file and node provided' % INDEX_FILENAME)
            exit(1)
        with open(INDEX_FILENAME) as fp:
            assets_index = json.load(fp)
            for config in assets_index.values():
                check_list.append([open(config['assets']), config['node']])

    if ignore is None:
        ignore = []
    else:
        ignore = [x.strip() for x in ignore.split(',')]

    error_count = 0

    for file, node in check_list:
        validator = create_assets_validator(
            node=node,
            ignore=ignore,
            fast=fast,
            progress=progress
        )

        data = json.load(file)

        for error in validator.iter_errors(instance=data):
            asset_position = error.absolute_path[0]
            token_name = '%s (%s)' % (
                data[asset_position].get('name'),
                data[asset_position].get('symbol')
            )
            field = '.'.join([str(x) for x in error.absolute_path][1:])
            logger.error("[E] %s: %s: %s" % (token_name, field, error.message))
            error_count += 1

        file.close()

    if not error_count:
        click.echo("[OK] Validation complete.")
        exit(0)

    click.echo("[FAIL] validation failed, see details above.")
    exit(1)


@main.command(name='request')
@click.option('--host', default="0.0.0.0", help="Kafka host")
@click.option('--port', default="9092", help="Kafka port")
def validate_messages(host, port):
    """
    Process validation requests from kafka
    """
    obj = KafkaAssetValidator(host, port)
    obj.process_message()


def _configure_logging(loglevel):
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'default': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s %(levelname)-8s %(message)s'
            }
        },
        'handlers': {
            'console': {
                '()': 'logging.StreamHandler',
                'stream': sys.stdout,
                'formatter': 'default'
            },
        },
        'loggers': {
            'jwallet_tools': {
                'level': loglevel,
                'handlers': ['console'],
            }
        }
    })


if __name__ == '__main__':
    main.main()
