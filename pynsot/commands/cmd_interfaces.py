# -*- coding: utf-8 -*-

"""
Sub-command for Interfaces.

In all cases ``data = ctx.params`` when calling the appropriate action method
on ``ctx.obj``. (e.g. ``ctx.obj.add(ctx.params)``)

Also, ``action = ctx.info_name`` *might* reliably contain the name of the
action function, but still not sure about that. If so, every function could be
fundamentally simplified to this::

    getattr(ctx.obj, ctx.info_name)(ctx.params)
"""

from __future__ import unicode_literals

from ..vendor import click
from ..util import get_result
from . import callbacks
from .cmd_networks import DISPLAY_FIELDS as NETWORK_DISPLAY_FIELDS


# Ordered list of 2-tuples of (field, display_name) used to translate object
# field names oto their human-readable form when calling .print_list().
DISPLAY_FIELDS = (
    ('id', 'ID'),
    ('device', 'Device'),
    ('name', 'Name'),
    ('mac_address', 'MAC'),
    ('addresses', 'Addresses'),
    ('attributes', 'Attributes'),
)

# Fields to display when viewing a single record.
VERBOSE_FIELDS = (
    ('id', 'ID'),
    ('device', 'Device'),
    ('name', 'Name'),
    ('mac_address', 'MAC'),
    ('addresses', 'Addresses'),
    ('speed', 'Speed'),
    ('type', 'Type'),
    ('parent_id', 'Parent ID'),
    ('attributes', 'Attributes'),
)


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """
    Interface objects.

    An Interface resource can represent a network interface attached to a
    Device. Working with interfaces is usually the device and an interface
    name.

    Interfaces can have any number of arbitrary attributes as defined below.
    """


# Add
@cli.command()
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this Network (format: key=value).',
    multiple=True,
    callback=callbacks.transform_attributes,
)
@click.option(
    '-b',
    '--bulk-add',
    metavar='FILENAME',
    help='Bulk add Networks from the specified colon-delimited file.',
    type=click.File('rb'),
    callback=callbacks.process_bulk_add,
)
@click.option(
    '-D',
    '--device',
    metavar='DEVICE_ID',
    type=int,
    help=(
        'Unique ID of the Device to which this Interface is attached.'
        '  [required]'
    )
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    help='The name of the Interface.  [required]',
)
@click.pass_context
def add(ctx, attributes, bulk_add, device_id, name):
    """
    Add a new Interface.

    You must provide a Device ID using the -d/--device-id option.

    When adding a new Interface, you must provide a value for the -n/--name
    option.

    If you wish to add attributes, you may specify the -a/--attributes
    option once for each key/value pair.
    """
    data = bulk_add or ctx.params

    # Enforce required options
    if bulk_add is None:
        if name is None:
            raise click.UsageError('Missing option "-n" / "--name"')
    ctx.obj.add(data)


# List
@cli.group(invoke_without_command=True)
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this Network (format: key=value).',
    multiple=True,
)
@click.option(
    '-d',
    '--delimited',
    is_flag=True,
    help='Display set query results separated by commas vs. newlines.',
    default=False,
    show_default=True,
)
@click.option(
    '-D',
    '--device',
    metavar='DEVICE_ID',
    type=int,
    help='Unique ID of the Device being retrieved.',
)
@click.option(
    '-e',
    '--description',
    metavar='DESCRIPTION',
    type=str,
    help='Filter by Interfaces matching this description.',
)
@click.option(
    '-g',
    '--grep',
    is_flag=True,
    help='Display list results in a grep-friendly format.',
    default=False,
    show_default=True,
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Interface being retrieved.',
)
@click.option(
    '-l',
    '--limit',
    metavar='LIMIT',
    help='Limit result to N resources.',
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    help='Filter to Interfaces matching this name.'
)
@click.option(
    '-N',
    '--natural-key',
    is_flag=True,
    help='Display list results by their natural key',
    default=False,
    show_default=True,
)
@click.option(
    '-o',
    '--offset',
    metavar='OFFSET',
    help='Skip the first N resources.',
)
@click.option(
    '-p',
    '--parent-id',
    metavar='PARENT_ID',
    type=int,
    help='Filter by integer of the ID of the parent Interface.',
)
@click.option(
    '-q',
    '--query',
    metavar='QUERY',
    help='Perform a set query using Attributes and output matching Networks.',
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    help='Unique ID of the Site this Interface is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.option(
    '-S',
    '--speed',
    metavar='SPEED',
    type=int,
    help='Filter by integer of Mbps of interface (e.g. 20000 for 20 Gbps)',
)
@click.option(
    '-t',
    '--type',
    metavar='TYPE',
    type=int,
    help='Filter by integer of the interface type (e.g. 6 for ethernet)',
)
@click.pass_context
def list(ctx, attributes, delimited, device, description, grep, id, limit,
         name, natural_key, offset, parent_id, query, site_id, speed, type):
    """
    List existing Interfaces for a Site.

    You must provide a Site ID using the -s/--site-id option.

    When listing Interfaces, all objects are displayed by default. You
    optionally may lookup a single Interfaces by ID using the -i/--id option.

    You may limit the number of results using the -l/--limit option.
    """
    data = ctx.params
    data.pop('delimited')  # We don't want this going to the server.

    # If we provide ID, show more fields
    if id is not None or all([device, name]):
        display_fields = VERBOSE_FIELDS
    else:
        display_fields = DISPLAY_FIELDS

    # If we aren't passing a sub-command, just call list(), otherwise let it
    # fallback to default behavior.
    if ctx.invoked_subcommand is None:
        if query is not None:
            results = ctx.obj.set_query(data)
            interfaces = get_result(results)
            interfaces = sorted(
                (i['device'], i['name']) for i in interfaces
            )
            interfaces = ['%s:%s' % obj for obj in interfaces]
            joiner = ',' if delimited else '\n'
            click.echo(joiner.join(interfaces))
        else:
            ctx.obj.list(
                data, display_fields=display_fields,
                verbose_fields=VERBOSE_FIELDS
            )


@list.command()
@click.pass_context
def addresses(ctx, *args, **kwargs):
    """Get addresses assigned to an Interface."""
    callbacks.list_subcommand(
        ctx, display_fields=NETWORK_DISPLAY_FIELDS, my_name=ctx.info_name
    )


@list.command()
@click.pass_context
def networks(ctx, *args, **kwargs):
    """Get networks attached to Interface."""
    callbacks.list_subcommand(
        ctx, display_fields=NETWORK_DISPLAY_FIELDS, my_name=ctx.info_name
    )


'''
# Remove
@cli.command()
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Network being deleted.',
    required=True,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Network is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def remove(ctx, id, site_id):
    """
    Remove a Network.

    You must provide a Site ID using the -s/--site-id option.

    When removing a Network, you must provide the unique ID using -i/--id. You
    may retrieve the ID for a Network by parsing it from the list of Networks
    for a given Site:

        nsot networks list --site-id <site_id> | grep <network>
    """
    data = ctx.params
    ctx.obj.remove(**data)


# Update
@cli.command()
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this Network (format: key=value).',
    multiple=True,
    callback=callbacks.transform_attributes,
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Network being updated.',
    required=True,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Network is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.option(
    '-A',
    '--add-attributes',
    'attr_action',
    flag_value='add',
    default=True,
    help=(
        'Causes attributes to be added. This is the default and providing it '
        'will have no effect.'
    )
)
@click.option(
    '-d',
    '--delete-attributes',
    'attr_action',
    flag_value='delete',
    help=(
        'Causes attributes to be deleted instead of updated. If combined with'
        'with --multi the attribute will be deleted if either no value is '
        'provided, or if attribute no longer has an valid values.'
    ),
)
@click.option(
    '-r',
    '--replace-attributes',
    'attr_action',
    flag_value='replace',
    help=(
        'Causes attributes to be replaced instead of updated. If combined '
        'with --multi, the entire list will be replaced.'
    ),
)
@click.option(
    '-m',
    '--multi',
    is_flag=True,
    help='Treat the specified attributes as a list type.',
)
@click.pass_context
def update(ctx, attributes, id, site_id, attr_action, multi):
    """
    Update a Network.

    You must provide a Site ID using the -s/--site-id option.

    When updating a Network you must provide the unique ID (-i/--id) and at
    least one of the optional arguments.

    The -a/--attributes option may be provided multiple times, once for each
    key-value pair. You may also specify the -a a single time and separate
    key-value pairs by a single comma.

    When modifying attributes you have three actions to choose from:

    * Add (-A/--add-attributes). This is the default behavior that will add
    attributes if they don't exist, or update them if they do.

    * Delete (-d/--delete-attributes). This will cause attributes to be
    deleted. If combined with --multi the attribute will be deleted if either
    no value is provided, or if the attribute no longer contains a valid value.

    * Replace (-r/--replace-attributes). This will cause attributes to
    replaced. If combined with -m/--multi and multiple attributes of the same
    name are provided, only the last value provided will be used.
    """
    if not any([attributes]):
        msg = 'You must supply at least one of the optional arguments.'
        raise click.UsageError(msg)

    data = ctx.params
    ctx.obj.update(data)
'''
