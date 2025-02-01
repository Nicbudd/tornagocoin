import player, games, global_state
from common import *
import re
import discord
from discord.ext import commands, tasks


# set up client ----------------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.check
async def globally_block_dms(ctx):
    return (ctx.guild is not None) or is_admin()


# commands ---------------------------------------------------------------------

@bot.hybrid_command()
async def hi(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.hybrid_command()
async def bal(ctx):
    p = await player.get(state, ctx)
    await p.send_status(ctx)

@bot.hybrid_command()
async def play(ctx, game):
    p = await player.get(state, ctx)
    await games.play(game, p, ctx)

@bot.hybrid_command()
async def testplay(ctx, game):
    p = await player.get(state, ctx)
    await games.play(game, p, ctx, testplay=True)



# admin commands ---------------------------------------------------------------

def is_admin():
    async def predicate(ctx):
        return ctx.author.id == ADMIN
    return commands.check(predicate)


@bot.hybrid_command()
@is_admin()
async def tickets(ctx, action: str, amount: int, user: discord.User):
    p = await player.get(state, ctx)

    p.refresh_tickets()
    
    action = action.lower()
    if action == "set":
        p.tickets = amount
        await p.send_status(ctx)
        p.save()
    elif action in ["add", "give"]:
        p.tickets += amount
        await p.send_status(ctx)
        p.save()
    elif action in ["take", "remove", "subtract", "sub"]:
        p.tickets -= amount
        await p.send_status(ctx)
        p.save()
    else:
        await ctx.send(f"Unknown command `{action}`")


@bot.hybrid_command()
@is_admin()
async def coins(ctx, action: str, amount: int, user: discord.User):
    p = await player.get(state, ctx)
    
    action = action.lower()
    if action == "set":
        p.coins = amount
        await p.send_status(ctx)
        p.save()
    elif action in ["add", "give"]:
        p.coins += amount
        await p.send_status(ctx)
        p.save()
    elif action in ["take", "remove", "subtract", "sub"]:
        p.coins -= amount
        await p.send_status(ctx)
        p.save()
    else:
        await ctx.send(f"Unknown command `{action}`")


# run client -------------------------------------------------------------------

state = global_state.load()

with open("data/discord_token.config") as fp:
    token = fp.read()
token = token.strip()

bot.run(token)