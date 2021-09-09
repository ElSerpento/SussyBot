# Import needed module
from random import randrange
from wand import image
import aiohttp
import json


# Returns a random spinning food url
async def food_gif_url():
    # Spinning food archives base (first) url
    food_url = 'https://archive.org/metadata/rotatingfood'

    # There are 5 rotating food archives, randomly choose
    # one of them.
    n = randrange(1, 5)
    if n == 1:
        food_url += '/'
    else:
        food_url += f'{n}/'

    # Make a GET request to the archive's metadata
    async with aiohttp.ClientSession() as session:
        async with session.get(food_url) as r:

            # Load the JSON response
            r = json.loads(await r.text())
            # Get a random gif's filename from the archive
            gif_name = r['files'][randrange(0, len(r['files']) - 1)]['name']

            # Do some string manipulation on the URL to get a direct link to the image
            dl_url = food_url.replace('metadata', 'download')
            dl_url += gif_name
            dl_url = dl_url.replace(' ', '%20')

            # Return the URL
            return dl_url


# Recursively content aware an image a specified amount of times. Img argument must be a Wand image.
# Returns a bytes object
async def content_aware(img, reps = 1):
    img.liquid_rescale(width=int(img.width * 0.5), height=int(img.height * 0.5), delta_x=1, rigidity=0)
    img.liquid_rescale(width=int(img.width * 2), height=int(img.height * 2), delta_x=1, rigidity=0)
    if reps == 1:
        return img
    else:
        return await content_aware(img, reps - 1)


# Deep fries an image recursively
async def deep_fry(img, reps):
    # Apply deep fry filters (Is this good, is this bad? i'm just going to leave it like it is)
    img.brightness_contrast(0, 33)
    img.local_contrast(1, 8)
    img.unsharp_mask(3, 5, 5)

    if reps == 1:
        return img
    else:
        return await deep_fry(img, reps - 1)

async def riir(img, append):
    
    # Clone the image, take half of its width
    clone = img.clone()
    w = int(img.width / 2) if not append is True else img.width

    # Crop the right half of the image and flip it
    img.crop(left=w, width=w, height=img.height)
    img.flop()

    # Crop the right half of the clone
    clone.crop(width=img.width, left=w)

    # Add clone to img (img on left, clone right) then return the result
    img.sequence.append(clone)
    img.concat()
    return img

async def leel(img, append):

    # Clone the image and take half its width
    clone = img.clone()
    w = int(img.width / 2) if not append is True else img.width

    # Delete the right half of the image
    img.crop(width=w, height=img.height)

    # Crop the clone to only its left side then flip it
    clone.crop(width=w)
    clone.flop()

    # Add clone to the right half of og image and return the result
    img.sequence.append(clone)
    img.concat()
    return img

async def hue_shift(img, rotation):

    # Keep brightness and saturation intact, only change the hue
    img.modulate(100, 100, rotation)
    return img