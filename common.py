import discord

# config -----------------------------------------------------------------------

ADMIN = 396730242460418058

# functions --------------------------------------------------------------------

def tornago(ctx):
    return discord.utils.get(ctx.bot.emojis, name="tornago")

async def author_color(ctx):
    user = await ctx.bot.fetch_user(ctx.author.id)
    return user.accent_color