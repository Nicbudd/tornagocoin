"""
Common shared library for all components of Tornago Coin project.
"""

import discord

# config -----------------------------------------------------------------------

ADMIN = 396730242460418058
GAMER_ROLE = 1312520586265886742

# functions --------------------------------------------------------------------
def tornago(ctx):
    """Gets the discord emoji for tornago."""
    return discord.utils.get(ctx.bot.emojis, name="tornago")

async def get_user(userid, ctx):
    """Grabs the user details from the discord client."""
    return await ctx.bot.fetch_user(userid)
