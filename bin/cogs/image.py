# Import needed modules
from bin.helpers import im, util
from discord.ext import commands
import asyncio
import discord
import random

class Image(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.description = 'Does various thing to an image of your choosing, or brings up an image for you.'


    # Determine the repetitions a command should do,
    # from an argument that could either be an url or the amount of reps.
    async def parse_reps(self, arg):
        # If the first arg is an url, it won't be decimal.
        # Therefore assume 1 if no reps specified.
        if not arg.isdecimal():
            return 1
        # If it IS decimal, we assume the user wanted to specify
        # repetitions. Convert the type and change the number if it's invalid.
        else:
            reps = int(arg)
            if reps > 10: reps = 10
            elif reps < 1: reps = 1
            return reps

    # Get the image to be modified and convert it
    # into a Wand image object
    async def parse_img(self, ctx):

        # Wait a bit so the embed shows up, if it's an attachment or link
        await asyncio.sleep(0.75)

        # Parse the user's message for the image they want modified
        img_url = await util.parse_msg(ctx.message)

        # If it couldn't be found, raise an error then return None
        if img_url is None:
            await ctx.send(embed=util.error_embed("Couldn't find your image"))
            return None

        # Get the image from its url and convert it into a Wand image
        img = await util.img_from_url(img_url)
        if img is None:
            await ctx.send(embed=util.error_embed("File type not supported"))
            return None
        
        # Return image
        return img


    @commands.command(name="contentaware", usage=('repetitions URL'
    '\nExample: **contentaware 4 [bunger image url]**' '\nThis command will contentaware an image of bunger'
    ' 4 times. You can also reply to a message with an embed, or attach an image instead of specifying an URL.'),
    help='Contentawares an image', description="Content aware scales an image, given it's not a gif.")
    async def content_aware(self, ctx, arg = '1'):

        # Get img referenced in user's message
        # Cancel if none found
        img = await self.parse_img(ctx)
        if not img:
            return

        # Trigger typing while the img is processed
        async with ctx.typing():

            # Get reps from arg
            reps = await self.parse_reps(arg)

            # Filter the image and upload to imgur
            img = await im.content_aware(img, reps)
            em = await util.embed_from_image(img, ctx.author.color, f'**Scaled {reps} time(s)!**')
            
            # Send embed
            await ctx.send(embed=em)


    @commands.command(name="deepfry", help='Deepfries an image', usage=('repetitions URL'
    '\nExample: **deepfry 4 [ploob image url]**' '\nThis command will deepfry ploob'
    ' 4 times. You can also reply to a message with an embed, or attach an image instead of specifying an URL.'))
    async def deep_fry(self, ctx, arg = '1'):

        # Parse img from the message
        # Cancel if none found
        img = await self.parse_img(ctx)
        if not img:
            return

        async with ctx.typing():
            
            # Get reps from arg
            reps = await self.parse_reps(arg)

            # Filter image and make embed
            img = await im.deep_fry(img, reps)
            em = await util.embed_from_image(img, ctx.author.color, f'**Deep fried {reps} time(s)!**')

            await ctx.send(embed=em)

    
    @commands.command(name='hueshift', help='Hue shifts an image', usage=('percent URL'
    '\nExample: **hueshift 50%\ imgur.whatever.gov/bossbaby.png**\n' 'This command will rotate the given '
    "image's hue by 50%\."))
    async def hue_shift(self, ctx, percent = None):
        
        img = await self.parse_img(ctx)
        if not img:
            return

        # If the percent arg is an url or is omitted, do a random number
        if not percent or not percent.isdecimal():
            percent = random.randrange(1, 100)
        
        # If the percent is invalid, replace it with a random number
        percent = int(percent)
        if percent > 100 or percent < 1:
            percent = random.randrange(1, 100)

        # Start typing as image is filtered
        async with ctx.typing():

            img = await im.hue_shift(img, percent)
            em = await util.embed_from_image(img, ctx.author.color, f'**Shifted hue by {percent}!**')

            # Send result
            await ctx.send(embed=em)


    @commands.group(name='random', case_insensitive=True, 
    description='Pulls a random image out of various sites')
    async def random(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(self.random)


    @random.command(name="person", help='Outputs a normal person :^)',
    description=('Takes a person from the This Person Does Not Exist website and deepfries and/or contentawares'
    ' them a random amount of times, up to a max of 5 for content aware scale and 3 for deepfry.'))
    async def person(self, ctx):

        async with ctx.typing():
            # Randomize CAS and deepfry repetitions
            reps_cas = random.randrange(0, 5)
            reps_deepfry = random.randrange(0, 3)

            # Cancel if None returned
            img = await util.img_from_url("https://thispersondoesnotexist.com/image")
            if img is None:
                return await ctx.send(embed=util.error_embed('Problem getting image!'))

            # Apply filters
            if reps_cas > 0:
                img = await im.content_aware(img, reps_cas)
            if reps_deepfry > 0:
                img = await im.deep_fry(img, reps_deepfry)

            # Create embed with filtered image
            description=f'**Scaled {reps_cas} time(s)!\nDeepfried {reps_deepfry} time(s)!**'
            em = await util.embed_from_image(img, ctx.author.color, description)
            
            await ctx.send(embed=em)


    @random.command(name="spinningfood", help='Posts spinning food',
    description='Takes a random gif of spinning food from the 5 archives and posts it.')
    async def spinning_food(self, ctx):

        async with ctx.typing():
            # Create embed with random url from spinning food archive and send it
            em = discord.Embed(color=ctx.author.color)
            em.set_image(url = await im.food_gif_url())
            await ctx.send(embed=em)


    # Create mirror group of commands.
    @commands.group(name='mirror', case_insensitive=True, description = 'Mirrors images, on either side.')
    async def mirror(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.mirror)


    @mirror.command(name='LeeL', help='MirrorsrorriM an image', usage=(' URL'
    '\nExample: **mirror LeeL [append] [img url]**'
    '\nMirrors an image with a copy of itself flipped to the other side. If "append" is skipped, '
    'it will mirror only half the image.'))
    async def leel(self, ctx, mode = None):

        # Parse the mode the user wants to run the command with
        if mode:
            if mode == 'append':
                mode = True

        # Get the desired image
        img = await self.parse_img(ctx)
        if not img:
            return

        async with ctx.typing():

            # Apply filters
            img = await im.leel(img, mode)
            em = await util.embed_from_image(img, ctx.author.color)

            # Send result
            await ctx.send(embed=em)


    @mirror.command(name='RiiR', help='srorriMirrors an image', usage=('URL'
    '\nExample: **mirror RiiR [append] [image url]**'
    '\nMirrors a flipped image with a copy of itself. If append is skipped it will only mirror '
    'half of the image, keeping the original size'))
    async def riir(self, ctx, mode = None):

        # Parse mirroring mode
        if mode:
            if mode == 'append':
                mode = True

        # Get image from context
        img = await self.parse_img(ctx)
        if not img:
            return

        async with ctx.typing():

            # Make image embed
            img = await im.riir(img, mode)
            em = await util.embed_from_image(img, ctx.author.color)

            # Send embed
            await ctx.send(embed=em)
