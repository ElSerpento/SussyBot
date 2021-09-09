# Import needed libraries
from inspect import iscoroutinefunction, getmembers
from discord.ext import commands
from datetime import datetime
from wand import image
import logging
import aiohttp
import discord
import json
import os

# Predefined emotes
speedL = "<a:SpeedL:876709171263832086>"
speedR = "<a:SpeedR:876709161675677767>"
explosione = "<a:explosione:876709202603688006>"
dumpyFren = "<a:dumpyFren:876709139089350667>"

# Log imgur uploads
logging.basicConfig(filename='imgur.log', level=logging.INFO)

# Get local UTC offset
def get_timezone():
    # Get string with local UTC offset
    s = datetime.now(tz=datetime.now().astimezone().tzinfo).strftime("UTC %z")
    # Add a colon between the hour and minute and return it
    m  = s[len(s)-2:len(s)]
    s = s[:-2]
    s += ":"
    s += m
    return s


# Method to convert 12h time to military format,
# with period being whether the hour is AM/PM.
def parse_time(hour, period):

    if period == "am":
        # If hour can't be turned into an int, return none.
        try:
            hour = int(hour)
        except:
            return None

        # No need to change AM time unless it's 12.
        # Return none if hour invalid.
        if hour == 12:
            hour = 0
        elif hour > 12:
            return None

    elif period == "pm":
        # If hour can't be casted, return None.
        try:
            hour = int(hour)
        except:
            return None
        
        # Shift hour by 12h, only if it's lower than 12.
        # If it's 12, don't change it.
        if hour == 12:
            pass
        elif hour > 12:
            return None
        elif hour > 0:
            hour += 12
        else:
            return None
    
    # Return hour as a string.
    return str(hour)


async def embed_from_image(img, color, text = None):
    result_url = await imgur_upload(img.make_blob())
    em = discord.Embed(color = color, description = text)
    em.set_image(url=result_url)
    return em
 

# Make an embed out of text and optionally the author
def make_embed(text, author=None):
    embed = discord.Embed(description=text, colour=discord.Colour.from_rgb(102, 120, 255))
    # If an author is specified, display their name and avatar
    if author:
        embed.set_author(name=author.display_name, icon_url=author.avatar_url)
    return embed


# Takes an image converted to a bytes object and uploads it to imgur, returning the image url.
async def imgur_upload(img_byte):
    # Define parameters for POST request
    url = "https://api.imgur.com/3/upload"
    payload = {"image": img_byte}

    # Define headers for aiohttp client
    # Get the Imgur API client ID from environment variable
    imgur_auth = {"Authorization": "Client-ID " + os.getenv("IMGUR_ID")}

    # Make post request, and return the response's link which would be the image's url
    # Log every upload
    async with aiohttp.ClientSession(headers=imgur_auth) as session:
        async with session.post(url=url, data=payload) as response:
            response = json.loads(await response.text())
            logging.info(f"response data: {response} Client-ID: {os.getenv('IMGUR_ID')}")
            return response["data"]["link"]


# Parse a message for any image an user might want to reference
async def parse_msg(msg):

    # Check if message has embeds
    if msg.embeds:
        # User embeds will only have the image property
        # when it's a "fancy" embed like a twitter image. So check for it.
        if msg.embeds[0].image.url:
            return msg.embeds[0].image.url
        # Otherwise just check the url, which will be the image link when
        # for example a discord image is linked.
        return msg.embeds[0].url

    # Attachments will always have a link, not much to do here.
    elif msg.attachments:
        return msg.attachments[0].url

    # If all options are empty check the replied message, if it exists.
    elif msg.reference:
        reply = await msg.channel.fetch_message(msg.reference.message_id)
        if reply.embeds:
            # Since it's a reply, the replied message can be made by a bot.
            # Since bots can create empty embeds, check for everything first.
            if reply.embeds[0].image:
                return reply.embeds[0].image.url
            elif reply.embeds[0].url:
                return reply.embeds[0].url

        elif reply.attachments:
            return reply.attachments[0].url

    # If there are no images found return None    
    else:
        return None


# Returns a wand image from a URL, given it's an image
async def img_from_url(url):
    # Have to do this because of some discord embed fuckery,
    # gives the imgur page instead of the direct image link. Adding
    # a file extension whether it's the actual file's or not seems to fix it so fuck it.
    if url.startswith('https://imgur.com/'):
        url = url.replace('imgur.com', 'i.imgur.com') + '.jpeg'
    if not await url_is_image(url):
        return None
    # Get image and return wand image object
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return image.Image(blob = await response.content.read())


# Function to make an embed for errors.
def error_embed(text):
    
    embed = discord.Embed(
    description=f"{speedL}{dumpyFren}{explosione} **{text}** {dumpyFren}{explosione}{speedR}", 
    colour=discord.Colour.from_rgb(255, 0, 0)
    )
    return embed


# Check if an url is an image.
async def url_is_image(url):
    async with aiohttp.ClientSession() as session:
            # Try making a HEAD request to the url
            try:
                async with session.head(url) as response:
                    # If the headers' content type is not image or is an animated image, return false
                    mimetype = response.headers["Content-Type"].lower()
                    if mimetype in ["image/gif", "image/apng"]:
                        return False
                    elif mimetype.startswith("image"):
                        return True
                    else:
                        return False
            # If argument is not a valid url return false
            except aiohttp.client.InvalidURL:
                print('invalid url')
                return False
