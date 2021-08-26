# Import needed libraries
import discord
import itertools
from discord.ext import commands

# Custom help command for the bot, so as to not use minimal or default.
# Built on top of the minimal one.
# Had to copy paste from the source code because there's no way to override just the lines i need to, haha...
class CustomHelpCommand(commands.MinimalHelpCommand):

    # Define "no category" string on init
    def __init__(self, **options):
        super().__init__(**options)
        self.no_category = "Other"
    
    # Replace send_pages method that is called by every help command,
    # so every help command is an embed.
    async def send_pages(self, footer = None):
        dest = self.get_destination()
        for page in self.paginator.pages:

            help_embed = discord.Embed(description=page, colour=discord.Colour.from_rgb(102, 120, 255))
            if footer is not None:
                help_embed.set_footer(text=self.get_opening_note().replace("`", "") + " (case sensitive)")

            await dest.send(embed=help_embed)

    # This is just the same method as default MinimalHelpCommand, except it
    # puts in the opening note as a parameter to send_note so it loads it as the footer.
    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        no_category = '\u200b{0.no_category}'.format(self)
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)

        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            self.add_bot_commands_formatting(commands, category)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages(self.get_opening_note())


    # Same as MinimalHelpCommand but with slight modifications
    async def send_group_help(self, group):

        self.paginator.add_line(group.description)
        self.paginator.add_line()

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        if filtered:
            self.paginator.add_line('**%s**' % self.commands_heading)
            for command in filtered:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_command_help(self, command):
        self.add_command_formatting(command)
        self.paginator.close_page()
        await self.send_pages()

    # Remove short help description off of command help.
    def add_command_formatting(self, command):
        if command.description:
            self.paginator.add_line(command.description, empty=True)

        signature = self.get_command_signature(command)
        if command.aliases:
            self.paginator.add_line(signature)
            self.add_aliases_formatting(command.aliases)
        else:
            self.paginator.add_line(signature, empty=True)

    # Remove opening note from default cog help
    async def send_cog_help(self, cog):
        bot = self.context.bot
        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        if cog.description:
            self.paginator.add_line(cog.description, empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        if filtered:
            self.paginator.add_line('**%s %s**' % (cog.qualified_name, self.commands_heading))
            for command in filtered:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()
        