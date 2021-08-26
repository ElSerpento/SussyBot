# Need to put actual errors on those... well, errors.

# Import needed modules
from bin.helpers.util import error_embed, make_embed, get_timezone, parse_time
from discord.ext import commands
from discord.ext import tasks
from datetime import datetime, timedelta
from durations_nlp import Duration

# Timezone string constant.
LOCAL_TIMEZONE = get_timezone()

class Alert(commands.Cog):

    # Start timer as soon as cog is initiated
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.description="Utility to ping a group of people for an event."
        self.count_time.start()

    # Executes code when a reaction is added.
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):

        # Only execute if the reaction's emoji is unicode
        # Allow only for length 1 cuz uhhh idk it causes an exception otherwise
        if reaction.emoji.is_unicode_emoji() and len(reaction.emoji.name) == 1:

            # If the emoji is :white_check_mark:, add user to message's notifs from self.db.
            if ord(reaction.emoji.name) == 0x02705:

                # Gets the channel and message that was reacted to.
                react_channel = self.bot.get_channel(reaction.channel_id)
                react_message = await react_channel.fetch_message(reaction.message_id)

                # Get pending alerts from database
                alerts = self.db.execute("SELECT * FROM alert")

                # Go through each alert
                for alert in alerts:
                    # If the reacted message matches an alert's ID, add the user to its notifs
                    if react_message.id == alert[1]:
                        self.db.execute("INSERT INTO notif_user (alert_id, user_id) VALUES(?, ?);", 
                        (react_message.id, reaction.user_id))
                        self.db.commit()

            # If the emoji added is :x: and the user has command perms, cancel the alert.
            elif ord(reaction.emoji.name) == 0x274C:

                # Check user perms.
                can_use_commands = False
                for role in reaction.member.roles:
                    if role.permissions.use_slash_commands:
                        can_use_commands = True
                
                if can_use_commands:

                    # Gets the channel and message that was reacted to.
                    react_channel = self.bot.get_channel(reaction.channel_id)
                    react_message = await react_channel.fetch_message(reaction.message_id)

                    # Get pending alerts
                    alerts = self.db.execute("SELECT * FROM alert")

                    # Iterate through alerts and find the reacted one.
                    for alert in alerts:
                        if react_message.id == alert[1]:
                            # Edit message to show it's cancelled
                            cancel_embed = make_embed("**SORRY GAMERS!! ALERT CANCELLED!!!**", react_message.author)
                            await react_message.edit(embed=cancel_embed)

                            # Delete alert and notifs entries from database, and end the loop
                            self.db.execute("DELETE FROM alert WHERE message_id = ?", (react_message.id,))
                            self.db.execute("DELETE FROM notif_user WHERE alert_id = ?", (react_message.id,))
                            self.db.commit()
                            break


    # Executes code when a reaction is removed.
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, reaction):

        # Only execute this if the emoji removed is white checkmark
        # Needs to be a single character cuz idk, unicode emojis be fucky or smn
        if reaction.emoji.is_unicode_emoji() and len(reaction.emoji.name) == 1:
            if ord(reaction.emoji.name) == 0x02705:

                # Gets the channel and message that was reacted to.
                react_channel = self.bot.get_channel(reaction.channel_id)
                react_message = await react_channel.fetch_message(reaction.message_id)

                # Get notifs
                notif_users = self.db.execute("SELECT * FROM notif_user")

                for notif in notif_users:
                    # If an alert message's id matches with reacted message,
                    if react_message.id == notif[0]:
                        # Remove user from notifs
                        self.db.execute("DELETE FROM notif_user WHERE user_id = ? AND alert_id = ?;", 
                        (reaction.user_id, notif[0]))
                        self.db.commit()


    # Executes code every minute, checks time to see if desired time
    # has been reached and sends a message when so.
    @tasks.loop(minutes=1)
    async def count_time(self):

        # Get pending alerts
        alerts = self.db.execute("SELECT * FROM alert;")

        # Iterate over every alert.
        for alert in alerts:
            # If destination time has been reached execute code below
            if datetime.now() >= alert[2]:

                # Cancel without pinging anyone if there are no reacts.
                if self.db.execute("SELECT COUNT (user_id) FROM notif_user WHERE alert_id = ?;", 
                (alert[1],)).fetchone()[0] == 0:
                    # Delete alert and notif entries from database
                    self.db.execute("DELETE FROM notif_user WHERE alert_id = ?;", (alert[1],))
                    self.db.execute("DELETE FROM alert WHERE message_id = ?;", (alert[1],))
                    self.db.commit()
                else:
                    # Get users to be notified
                    notify_list = self.db.execute("SELECT * FROM notif_user WHERE alert_id = ?", (alert[1],))

                    # Add an user mention to message for each user in notifs
                    shout = ""
                    for user_id in notify_list:
                        tmp_user = await self.bot.fetch_user(user_id[1])
                        shout += tmp_user.mention

                    # extra text for funny, different if there's a label
                    if alert[3]:
                        shout += "\n**IT'S TIME FOR " + alert[3].upper() + "!!!!!**"
                    else:
                        shout += "\n**IT'S TIME, STINKY!!!!!!!!!**"

                    # Get the channel to shout at
                    shout_channel = self.bot.get_channel(alert[0])

                    # If message for some reason is missing, delete from the database all of it's entries and
                    # return, so as to not send with a None object.
                    if not shout_channel:
                        self.db.execute("DELETE FROM notif_user WHERE alert_id = ?;", (alert[1],))
                        self.db.execute("DELETE FROM alert WHERE message_id = ?;", (alert[1],))
                        self.db.commit()
                        return print("Shout channel not found... rip")

                    # Send message and delete alert and related entries from database.
                    await shout_channel.send(shout)
                    self.db.execute("DELETE FROM notif_user WHERE alert_id = ?;", (alert[1],))
                    self.db.execute("DELETE FROM alert WHERE message_id = ?;", (alert[1],))
                    self.db.commit()


    # Returns message stating current timezone.
    @commands.command(name="timezone", help="Shows working timezone (kind of)", description=("This bot was done "
    "by a lazyass, so it has no support for timezones other than the one used by "
    "the system hosting this bot. Therefore, this is here to make your life the most insignificant bit easier."))
    async def show_timezone(self, ctx):

        # Only allow use if author can use commands.
        can_use_commands = False
        for role in ctx.author.roles:
            if role.permissions.use_slash_commands:
                can_use_commands = True
        
        # Send message with local timezone and time.
        if can_use_commands:
            now = datetime.now().strftime("%y/%m/%d %I:%M%p")
            await ctx.send(embed=make_embed(f"**Working timezone is {LOCAL_TIMEZONE}!! ({now})**"))


    # Sets a time for stored users to be pinged at.
    @commands.command(name="sendalert", usage=("**on** month/day hour:minute **for** event."
    "\nExample: sendalert on #/21 1:00PM for barbie watchalong"
    "\nA number replaced with # will be the current date's. If 'in' is used instead of 'on', you can say a duration instead of a date."),
    help="Sends an alert message",
    description=("Send a message that pings users at the specified time, "
    "as long as they don't remove their reaction. To cancel an alert simply react to it with :x:."))
    async def send_alert(self, ctx, arg1, *, args):

        # See if author can use commands.
        can_use_commands = False
        for role in ctx.author.roles:
            if role.permissions.use_slash_commands:
                can_use_commands = True
        
        # Turn first arg lowercase so command is case insensitive
        arg1 = arg1.lower()
        
        if can_use_commands:

            # Execute if an alert label is present
            if "for" in args.lower():
                # Split command into before, and after label.
                # If "for" is present but no label, return error.
                try:
                    time, label = args.lower().split(" for ")
                except ValueError as e:
                    return await ctx.send(embed=error_embed(e))
                
                # If input is date, split month/day and hour:minute
                if arg1 == "on":
                    time = time.rsplit()
            else:
                # If there's no label,
                # assign it to none.
                label = None
                if arg1 == "on":
                    time = args.rsplit()
                else:
                    time = args

            # If first argument is "on" we process
            # the input time as a date
            if arg1 == "on":

                # Initiate arg variables
                day = None
                hour = None

                # Split args so month/day and hour/minute can be manipulated separatedly
                if "/" in time[0] and ":" in time[1]:
                    day = time[0].rsplit("/")
                    hour = time[1].rsplit(":")
                else:
                    return await ctx.send(embed=make_embed('sendalert ' + self.send_alert.usage))
                
                # Get military hour if input in 12h format

                # If there's no space between hour and time period,
                # process string and remove period from it.
                if not hour[1].isnumeric():
                    if "am" in hour[1].lower():
                        hour[0] = parse_time(hour[0], "am")
                        hour[1] = hour[1].lower().replace("am", "")
                    elif "pm" in hour[1].lower():
                        hour[0] = parse_time(hour[0], "pm")
                        hour[1] = hour[1].lower().replace("pm", "")

                # If there's space between hour and period, simply get
                # the time.
                elif len(time) == 3:
                    if time[2].lower() == "am":
                        hour[0] = parse_time(hour[0], "am")
                    elif time[2].lower() == "pm":
                        hour[0] = parse_time(hour[0], "pm")
                
                if time is None:
                    return await ctx.send("no")

                # Process "#" modifiers, changing them to current time.
                if "#" in day or "#" in hour:
                    for i, s in enumerate(day):
                        if s == "#": day[i] = str(datetime.now().month) if i == 0 else str(datetime.now().day)
                    for i, s in enumerate(hour):
                        if s == "#": hour[i] = str(datetime.now().hour) if i == 0 else str(datetime.now().minute)

                # If any of the elements are not numbers return and shit talk the user.
                if not day[0].isdigit() or not day[1].isdigit() or not hour[0].isdigit() or not hour[1].isdigit():
                    return await ctx.send(embed=make_embed('sendalert ' + self.send_alert.usage))

            # If first argument is "in" the time input is
            # a duration.
            elif arg1 == "in":
                
                # Parse the string using duration_nlb module to get the duration.
                # if it's invalid return an error.
                try:
                    time = Duration(time).to_seconds()
                except:
                    return await ctx.send(embed=make_embed('sendalert ' + self.send_alert.usage))
                
                # Only allow for results equal or above 1 second
                if time >= 1:
                    time = timedelta(seconds=time)
                else:
                    return await ctx.send(embed=error_embed("**Please input more than 1 second!**"))

            # If first argument is neither "in" or "on", it's invalid
            else:
                # fill this with an actual error later
                return await ctx.send(embed=make_embed('sendalert ' + self.send_alert.usage))

            # If there's no shout_channel entry for this guild, notify and return
            if self.db.execute("SELECT COUNT(channel_id) FROM shout_channel WHERE (guild_id = ?);", 
            (ctx.guild.id,)).fetchone()[0] == 0:
                return await ctx.send(embed=error_embed("Wrong channel, or bot channel hasn't been assigned!\
                \nAssign a channel with setchannel channelname!!!"))

            # Get this guild's shout channel
            shout_channel_id = self.db.execute("SELECT channel_id FROM shout_channel WHERE guild_id = ?", 
            (ctx.guild.id,)).fetchone()[0]
            shout_channel = self.bot.get_channel(shout_channel_id)

            # Set alert time according to input method
            if arg1 == "on":
                # Set alert time to specified date
                now = datetime.now()
                alert_time = datetime(year=now.year, month=int(day[0]), 
                day=int(day[1]), hour=int(hour[0]), minute=int(hour[1]))
            else:
                # Set alert to current time, plus specified duration
                alert_time = datetime.now() + time

            # Send alert message and store into database, varying depending on whether alert has a label
            if label:
                msg_content = ("**React to this message with :white_check_mark: " +
                "if you wanna be pinged at {0} ({1}) for {2}!!!**".format(alert_time.strftime("%m/%d %I:%M%p"), LOCAL_TIMEZONE, label) +
                "\n> To cancel this alert, an user with command permissions can react to it with :x:!")

                alert_message = await shout_channel.send(embed=make_embed(msg_content, ctx.author))

                self.db.execute("INSERT INTO alert (channel_id, message_id, alert_time, label) VALUES (?, ?, ?, ?)",
                (alert_message.channel.id, alert_message.id, alert_time, label))

            else:
                msg_content = ("**React to this message with :white_check_mark: " +
                    "if you wanna be pinged at {0}!!!** ({1})".format(alert_time.strftime("%m/%d %I:%M%p"), LOCAL_TIMEZONE) +
                    "\n> To cancel this alert, an user with command permissions can react to it with :x:!")

                alert_message = await shout_channel.send(embed=make_embed(msg_content, ctx.author))

                self.db.execute("INSERT INTO alert (channel_id, message_id, alert_time) VALUES (?, ?, ?)", 
                (alert_message.channel.id, alert_message.id, alert_time))

            self.db.commit()


    # Sets a channel to send the announcements to
    @commands.command(name="setchannel", usage=("channelname\n**Example: setchannel #general** \nWill " 
    "make every sendalert message go to the general channel."),
    help="Sets a channel for alerts to be sent to",
    description=("When the bot joins, this command needs to be used to tell it where to send alert messages."
    "\nIMPORTANT: You need channel managing permissions to use this command."))
    async def set_channel(self, ctx, arg_channel):

        # Only allow the use of this command if the user can manage channels and use commands.
        can_use_commands = False
        can_manage_channels = False
        for role in ctx.author.roles:
            if role.permissions.manage_channels:
                can_manage_channels = True
            if role.permissions.use_slash_commands:
                can_use_commands = True

        if can_manage_channels and can_use_commands:

            # Account for the user tagging the channel instead
            # of just typing the name (thx evyn :D)
            is_tag = False
            if "#" in arg_channel:
                new_arg = ""
                for char in arg_channel:
                    if char.isdigit():
                        new_arg += char
                arg_channel = new_arg
                is_tag = True

            # If tagged, use ID to get channel and set it if it's in the current guild.
            if is_tag:
                try:
                    arg_channel = await self.bot.fetch_channel(arg_channel)
                except:
                    return await ctx.send(embed=error_embed("**Channel does not exist!!**"))

                # If it's in the guild insert into database, otherwise notify user
                if arg_channel in ctx.guild.text_channels:
                    # If database entry exists simply update the channel
                    if self.db.execute("SELECT COUNT(channel_id) FROM shout_channel WHERE guild_id = ?", 
                    (ctx.guild.id,)).fetchone()[0] >= 1:
                        self.db.execute("UPDATE shout_channel SET channel_id = ? WHERE guild_id = ?", 
                        (arg_channel.id, ctx.guild.id))
                        self.db.commit()
                    # Otherwise, insert new entry into shout_channel
                    else:
                        self.db.execute("INSERT INTO shout_channel (channel_id, guild_id) VALUES(?, ?)", 
                        (arg_channel.id, ctx.guild.id))
                        self.db.commit()
                    await ctx.send(embed=make_embed("Set bot channel to **{0.name}**!!!".format(arg_channel)))
                else:
                    await ctx.send(embed=error_embed("**Channel does not exist!!!**"))

            else:
                # If just named, simply iterate through guild's channel names and set
                # if there is a match.
                channel_names = [channel.name for channel in ctx.guild.channels]
                if arg_channel.lower() in channel_names:
                    for channel in ctx.guild.text_channels:
                        if arg_channel.lower() == channel.name:
                            # Update if there's already an entry for the channel, otherwise insert a new one.
                            if self.db.execute("SELECT COUNT(channel_id) FROM shout_channel WHERE guild_id = ?", 
                            (ctx.guild.id,)).fetchone()[0] >= 1:
                                self.db.execute("UPDATE shout_channel SET channel_id = ? WHERE guild_id = ?", 
                                (channel.id, ctx.guild.id))
                                self.db.commit()
                            else:
                                self.db.execute("INSERT INTO shout_channel (channel_id, guild_id) VALUES(?, ?)", 
                                (channel.id, ctx.guild.id))
                                self.db.commit()
                            await ctx.send(embed=make_embed("Set bot channel to **{0}**!!!".format(arg_channel)))
                else:
                    await ctx.send(embed=error_embed("**Channel does not exist!!!**"))