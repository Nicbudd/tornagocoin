import discord

# config -----------------------------------------------------------------------

ADMIN = 396730242460418058
GAMER_ROLE = 1312520586265886742

# functions --------------------------------------------------------------------

def tornago(ctx):
    return discord.utils.get(ctx.bot.emojis, name="tornago")

async def get_user(self, userid, ctx):
    return await ctx.bot.fetch_user(userid)