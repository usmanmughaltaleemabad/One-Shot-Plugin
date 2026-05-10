#!/usr/bin/env python3
"""
Gap 4: Slash Command / CLI Scaffolding

Separates business logic from platform-specific wrappers:
- Discord: @bot.command() wrapper calling pure service
- Slack: app.command('/...', ...) wrapper calling pure service
- Telegram: telegram.ext.CommandHandler wrapper
- CLI (Go/Python/Node): Cobra/Click/Commander wrappers

Input: Business logic code, target platform (discord/slack/telegram/cli)
Output: Pure service + platform-specific command file + tests
"""

import sys
from typing import Dict, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class SlashCommandScaffolder:
    """Generates platform-specific command wrappers around pure business logic."""

    def __init__(self, platform: str, language: str = 'python'):
        self.platform = platform.lower()  # discord, slack, telegram, cli
        self.language = language.lower()  # python, go, typescript, etc.

    def scaffold(self, feature_name: str, service_code: str, command_description: str = '') -> Dict[str, str]:
        """
        Generate service + command files.

        Args:
            feature_name: Feature name (e.g., 'rate_limiter')
            service_code: Pure business logic code
            command_description: Description for command help text

        Returns:
            Dict mapping filepath -> content
        """
        files = {}

        # Always generate pure service file
        files[f'{self.platform}/{feature_name}_service.py'] = service_code

        # Generate platform-specific wrapper
        if self.platform == 'discord':
            files[f'{self.platform}/{feature_name}_command.py'] = self._generate_discord_wrapper(
                feature_name, command_description
            )
        elif self.platform == 'slack':
            files[f'{self.platform}/{feature_name}_slash_command.py'] = self._generate_slack_wrapper(
                feature_name, command_description
            )
        elif self.platform == 'telegram':
            files[f'{self.platform}/{feature_name}_handler.py'] = self._generate_telegram_wrapper(
                feature_name, command_description
            )
        elif self.platform == 'cli':
            files[self._get_cli_command_path(feature_name)] = self._generate_cli_wrapper(
                feature_name, command_description
            )

        # Generate tests
        files[f'tests/test_{self.platform}_{feature_name}_service.py'] = self._generate_service_tests(
            feature_name
        )
        files[f'tests/test_{self.platform}_{feature_name}_command.py'] = self._generate_command_tests(
            feature_name
        )

        return files

    def _generate_discord_wrapper(self, feature_name: str, description: str) -> str:
        """Generate Discord bot command wrapper."""
        return f'''"""Discord command wrapper for {feature_name}"""

import discord
from discord.ext import commands
from .{feature_name}_service import {self._to_pascal_case(feature_name)}Service

service = {self._to_pascal_case(feature_name)}Service()


class {self._to_pascal_case(feature_name)}Cog(commands.Cog):
    """Commands for {feature_name}"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='{feature_name}', help='{description}')
    async def {feature_name}_command(self, ctx, *args):
        """
        {description}

        Usage: !{feature_name} [args]
        """
        try:
            result = await service.process(*args)
            await ctx.send(f"✅ {{result}}")
        except Exception as e:
            logger.error(f"Error in {feature_name}: {{e}}")
            await ctx.send(f"❌ Error: {{str(e)}}")


async def setup(bot):
    """Load the {feature_name} cog"""
    await bot.add_cog({self._to_pascal_case(feature_name)}Cog(bot))
'''

    def _generate_slack_wrapper(self, feature_name: str, description: str) -> str:
        """Generate Slack slash command wrapper."""
        return f'''"""Slack slash command wrapper for {feature_name}"""

from slack_bolt import App
from slack_bolt.context import BoltContext
from slack_bolt.request import BoltRequest
from .{feature_name}_service import {self._to_pascal_case(feature_name)}Service
import logging

logger = logging.getLogger(__name__)
service = {self._to_pascal_case(feature_name)}Service()


def register_commands(app: App):
    """Register /{feature_name} slash command"""

    @app.command("/{feature_name}")
    def handle_{feature_name}(ack, command: dict, say):
        """Handle /{feature_name} slash command"""
        ack()

        try:
            args = command.get("text", "").split()
            result = service.process(*args)

            say(f":white_check_mark: {feature_name} result: {{result}}")
        except Exception as e:
            logger.error(f"Error in /{feature_name}: {{e}}")
            say(f":x: Error: {{str(e)}}")


# Usage in main app:
# from slack_bolt import App
# from .{feature_name}_slash_command import register_commands
#
# app = App(token=os.getenv("SLACK_BOT_TOKEN"), signing_secret=os.getenv("SLACK_SIGNING_SECRET"))
# register_commands(app)
'''

    def _generate_telegram_wrapper(self, feature_name: str, description: str) -> str:
        """Generate Telegram bot handler."""
        return f'''"""Telegram bot handler for {feature_name}"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from .{feature_name}_service import {self._to_pascal_case(feature_name)}Service
import logging

logger = logging.getLogger(__name__)
service = {self._to_pascal_case(feature_name)}Service()


async def {feature_name}_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /{feature_name} command.

    {description}
    """
    try:
        args = context.args or []
        result = await service.process(*args)

        await update.message.reply_text(f"✅ {{result}}")
    except Exception as e:
        logger.error(f"Error in /{feature_name}: {{e}}")
        await update.message.reply_text(f"❌ Error: {{str(e)}}")


def get_handler() -> CommandHandler:
    """Get the CommandHandler for registration with dispatcher"""
    return CommandHandler("{feature_name}", {feature_name}_handler)


# Usage in main bot:
# from telegram.ext import Dispatcher
# from .{feature_name}_handler import get_handler
#
# dispatcher = Dispatcher(...)
# dispatcher.add_handler(get_handler())
'''

    def _generate_cli_wrapper(self, feature_name: str, description: str) -> str:
        """Generate CLI command wrapper (Python Click style)."""
        return f'''"""CLI command wrapper for {feature_name}"""

import click
from .{feature_name}_service import {self._to_pascal_case(feature_name)}Service

service = {self._to_pascal_case(feature_name)}Service()


@click.command('{feature_name}')
@click.argument('args', nargs=-1)
@click.help_option('-h', '--help')
def {feature_name}_cli(args):
    """
    {description}

    Usage:
      cli {feature_name} [args...]
    """
    try:
        result = service.process(*args)
        click.secho(f"✅ {{result}}", fg='green')
    except Exception as e:
        click.secho(f"❌ Error: {{str(e)}}", fg='red')


if __name__ == '__main__':
    {feature_name}_cli()
'''

    def _get_cli_command_path(self, feature_name: str) -> str:
        """Get the CLI command file path based on language."""
        if self.language == 'go':
            return f'cmd/{feature_name}/main.go'
        elif self.language == 'typescript':
            return f'src/commands/{feature_name}.ts'
        else:
            return f'cli/commands/{feature_name}.py'

    def _generate_service_tests(self, feature_name: str) -> str:
        """Generate unit tests for pure service."""
        return f'''"""Unit tests for {feature_name} service"""

import pytest
from {self.platform}.{feature_name}_service import {self._to_pascal_case(feature_name)}Service


@pytest.fixture
def service():
    """Create service instance for testing"""
    return {self._to_pascal_case(feature_name)}Service()


class Test{self._to_pascal_case(feature_name)}Service:
    """Tests for {feature_name} service"""

    def test_initialization(self, service):
        """Test service initializes correctly"""
        assert service is not None

    def test_process_basic(self, service):
        """Test basic process() call"""
        result = service.process()
        assert result is not None

    def test_process_with_args(self, service):
        """Test process() with arguments"""
        result = service.process("arg1", "arg2")
        assert isinstance(result, (str, dict, list))

    @pytest.mark.asyncio
    async def test_process_async(self, service):
        """Test async process if applicable"""
        # Uncomment if service.process is async:
        # result = await service.process()
        # assert result is not None
        pass
'''

    def _generate_command_tests(self, feature_name: str) -> str:
        """Generate integration tests for command wrapper."""
        return f'''"""Integration tests for {feature_name} command wrapper"""

import pytest


@pytest.mark.integration
class Test{self._to_pascal_case(feature_name)}Command:
    """Tests for {feature_name} command integration"""

    def test_command_registration(self):
        """Test command is registered correctly"""
        # Test that command can be discovered
        pass

    def test_command_help_text(self):
        """Test command help is available"""
        # Test --help or /help output
        pass

    def test_command_error_handling(self):
        """Test command handles errors gracefully"""
        # Test error message display
        pass
'''

    @staticmethod
    def _to_pascal_case(snake_str: str) -> str:
        """Convert snake_case to PascalCase."""
        return ''.join(word.capitalize() for word in snake_str.split('_'))


def main():
    """Test slash command scaffolding."""
    with timed_run("slash_command_scaffolder") as timer:
        logger.debug("Testing slash command scaffolding")

        test_service_code = '''"""Pure business logic for rate limiter"""

class RateLimiterService:
    def __init__(self, requests_per_minute=10):
        self.rpm = requests_per_minute

    async def process(self, user_id):
        # Check rate limit for user_id
        return f"User {{user_id}} has {{self.rpm}} requests remaining"
'''

        scaffolder = SlashCommandScaffolder('discord', 'python')
        files = scaffolder.scaffold(
            'rate_limiter',
            test_service_code,
            'Check rate limit for a user'
        )

        logger.debug(f"Generated {len(files)} command files")
        for filepath in files:
            print(f"  - {filepath}")

        check_budget("slash_command_scaffolder", timer.elapsed_ms, logger)

    logger.debug(f"slash_command_scaffolder completed in {timer.elapsed_ms:.0f}ms")


if __name__ == '__main__':
    main()
