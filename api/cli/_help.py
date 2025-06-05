import logging
import click

def _show_main_help(ctx):
    """Show automatically generated main help"""
    click.echo("Luna CLI - Project Management Tool")
    click.echo()
    click.echo("Available commands:")

    # Get all registered commands and show them
    for name, command in sorted(ctx.command.commands.items()):
        if name != 'interactive':  # Skip the interactive command in main help
            help_text = command.get_short_help_str() or "No description available"
            click.echo(f"  {name:<20} {help_text}")

    click.echo()
    click.echo("Usage examples:")
    click.echo("  python -m src.script.main project list")
    click.echo("  python -m src.script.main integration create my-local local")
    click.echo("  python -m src.script.main interactive    # Start interactive mode")
    click.echo()
    click.echo("Use 'python -m src.script.main <command> --help' for detailed help")


def _show_command_tree(ctx):
    """Show a tree view of all commands"""
    click.echo("\n" + "=" * 50)
    click.echo("COMMAND TREE")
    click.echo("=" * 50)

    cli_ctx = ctx.find_root()
    subparsers = ctx.obj.get('subparsers', {})

    for group_name, group_cmd in sorted(cli_ctx.command.commands.items()):
        if group_name == 'interactive':
            continue

        click.echo(f"\n📁 {group_name}")

        commands = []

        # Try to get commands from the group
        if hasattr(group_cmd, 'commands') and group_cmd.commands:
            commands = list(group_cmd.commands.items())
        elif group_name in subparsers:
            # Try to get from subparser
            try:
                subparser_group = subparsers[group_name].get_subparser()
                if hasattr(subparser_group, 'commands'):
                    commands = list(subparser_group.commands.items())
            except Exception as e:
                logging.getLogger("TreeGeneration").error(f"Error getting commands for {group_name}: {e}")

        if commands:
            for i, (cmd_name, cmd) in enumerate(commands):
                is_last = i == len(commands) - 1
                prefix = "└── " if is_last else "├── "
                click.echo(f"   {prefix}{cmd_name}")
        else:
            click.echo("   └── (no commands found)")


def _get_command_params_info(cmd):
    """Generate parameter info string for a command"""
    parts = []

    if hasattr(cmd, 'params'):
        for param in cmd.params:
            if isinstance(param, click.Argument):
                if param.required:
                    parts.append(f"<{param.name}>")
                else:
                    parts.append(f"[{param.name}]")
            elif isinstance(param, click.Option):
                if param.is_flag:
                    parts.append(f"[{param.opts[0]}]")
                else:
                    opt_name = param.opts[0]
                    if param.required:
                        parts.append(f"{opt_name} <value>")
                    else:
                        parts.append(f"[{opt_name} <value>]")

    return " ".join(parts)


def _generate_command_example(group_name, cmd_name, cmd):
    """Auto-generate realistic examples for commands"""
    examples = {
        # Project examples
        ('project', 'create'): 'project create my-app --emoji 🚀',
        ('project', 'list'): 'project list --sort name',
        ('project', 'delete'): 'project delete my-app --yes',
        ('project', 'show'): 'project show my-app',
        ('project', 'add_integration'): 'project add_integration my-app local-files',
        ('project', 'remove_integration'): 'project remove_integration my-app local-files',

        # Integration examples
        ('integration', 'create'): 'integration create local-files local --emoji 📁',
        ('integration', 'list'): 'integration list --sort name',
        ('integration', 'delete'): 'integration delete local-files --yes',
        ('integration', 'show'): 'integration show local-files',
        ('integration', 'modules'): 'integration modules',

        # Project Integration examples
        ('project_integration', 'add'): 'project_integration add my-app local-files',
        ('project_integration', 'remove'): 'project_integration remove my-app local-files --yes',
        ('project_integration', 'list'): 'project_integration list',
        ('project_integration', 'show'): 'project_integration show my-app-local-files',

        # Database examples
        ('database', 'list'): 'database list',
        ('database', 'show'): 'database show sqlite',
        ('database', 'tests'): 'database tests sqlite',
        ('database', 'clear'): 'database clear sqlite --yes',
    }

    return examples.get((group_name, cmd_name))