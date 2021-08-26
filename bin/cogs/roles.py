from discord.ext import commands
from bin.helpers import util

class Roles(commands.Cog):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.description = 'For automanaging roles'

    # Executes code when a reaction is added.
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):

        # Go further only if reacted with :white_check_mark:
        if reaction.emoji.is_unicode_emoji() and len(reaction.emoji.name) == 1:
            if ord(reaction.emoji.name) == 0x02705:

                # Get the roleopt message
                react_channel = self.bot.get_channel(reaction.channel_id)
                role_msg = self.db.execute("SELECT * FROM rolepost WHERE msg_id = ?;", (reaction.message_id,)).fetchone()

                # If the reacted message was a roleopt message, role_msg shouldn't be None. If it is, return.
                # Otherwise get the role given by the message. 
                if role_msg:
                    opt_role = react_channel.guild.get_role(role_msg[1])
                else: return

                # Add role to member
                if opt_role:
                    if not opt_role in reaction.member.roles:
                        await reaction.member.add_roles(opt_role)


    # Executes code when a reaction is removed.
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, reaction):

        # Only execute this if the emoji removed is white checkmark
        if reaction.emoji.is_unicode_emoji() and len(reaction.emoji.name) == 1:
            if ord(reaction.emoji.name) == 0x02705:

                # Gets the role for the message
                react_channel = self.bot.get_channel(reaction.channel_id)
                role_msg = self.db.execute("SELECT * FROM rolepost WHERE msg_id = ?;", (reaction.message_id,)).fetchone()

                # Continue only if the message given was a roleopt message (ie if it could be pulled from the database)
                if role_msg:
                    opt_role = react_channel.guild.get_role(role_msg[1])
                else: return

                # Remove the role from the user who reacted, if they have it.
                if opt_role:
                    member = react_channel.guild.get_member(reaction.user_id)
                    if member and opt_role in member.roles:
                        await member.remove_roles(opt_role)
        

    @commands.command(name='roleopt', usage=('role \nExample: roleopt bitch will give whoever '
    'reacts to the created message the @bitch role.'), help='Helps users in opt for a role',
    description=('Sends a message upon usage, which if reacted with :white_check_mark: '
    'will give the user who reacted the role. If said reaction is removed it will also remove this role'))
    async def role_opt(self, ctx, *args):

        # Ensure command can only be used if user can manage roles
        for role in ctx.author.roles:
            manage_roles = False
            if role.permissions.manage_roles:
                manage_roles = True
        if not manage_roles:
            return

        # Point out usage if there's no role input
        if not args:
            return await ctx.send(embed=util.error_embed('You have to specify a role!'))

        # convert args (tuple with each word as element) to a single string
        # if there's more than 1 word. else just take that word.
        if len(args) > 1:
            input_role = ''
            for i, arg in enumerate(args):
                input_role += arg
                if not i == len(args) - 1:
                    input_role += ' '
        else:
            input_role = args[0]

        # Well. There's really no point for this command if you do this is there.
        if input_role == '@everyone':
            return await ctx.send(embed=util.error_embed('no'))

        # Process arg in the case that the role got tagged instead of named
        if input_role.startswith('<@&') and input_role.endswith('>'):
            if len(args) == 1:
                input_role = int(input_role.strip('<@&>'))
                input_role = ctx.guild.get_role(input_role).name

                if input_role is None:
                    return await ctx.send(embed=util.error_embed('Role not found, poopoohead'))

        # Get a list of roles in guild
        roles = ctx.guild.roles

        # If there's a role whose name matches with the arg's role, send roleopt message.
        for role in roles:
            if role.name == input_role:
                msg = await ctx.send(embed=util.make_embed((f"Ok. {role.name} role. Who wants it? and yes, i'm giving it away. " 
                "Remember, react with :white_check_mark: to opt in, "
                "and remove reaction to opt out of the role."), author=ctx.author))

                self.db.execute('INSERT INTO rolepost (msg_id, role_id) VALUES(?, ?)', (msg.id, role.id))
                self.db.commit()
