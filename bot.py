import player, games, global_state, barobets
from common import *

import datetime as dt
import re

import discord
from discord.ext import commands, tasks
import typing


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

def is_admin():
    async def predicate(ctx):
        return ctx.author.id == ADMIN
    return commands.check(predicate)

# commands ---------------------------------------------------------------------

@bot.hybrid_command()
async def hi(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.hybrid_command()
async def bal(ctx):
    p = await player.get(state, ctx)
    await p.send_status(ctx)

@bot.hybrid_command()
async def leaderboard(ctx):
    tor = tornago(ctx)

    players = state.get_players().values()
    players = sorted(players, key=lambda x: x.net_worth(), reverse=True)

    s = ""
    for p in players:
        user = await ctx.bot.fetch_user(p.userid)
        s += f"{p.net_worth()} ({p.get_coins()} {tor}) - {user.name}\n"

    em = discord.Embed(title="**Leaderboard** (by net worth)", description=s)

    await ctx.send(embed=em)



@bot.hybrid_command()
async def buy_tickets(ctx, count: int):
    p = await player.get(state, ctx)
    for i in range(count):
        p.buy_ticket()
    await p.send_status(ctx)

@bot.hybrid_command()
async def play(ctx, game):
    await games.play(game, state, ctx)

@bot.hybrid_command()
async def testplay(ctx, game):
    await games.play(game, state, ctx, testplay=True)

@bot.hybrid_command()
async def d6(ctx):
    await games.play("d6", state, ctx)

@bot.hybrid_command()
async def d20(ctx):
    await games.play("d20", state, ctx)

@bot.hybrid_command()
async def l8(ctx):
    await games.play("l8", state, ctx)

@bot.hybrid_command()
async def lotto(ctx):
    await games.play("lotto", state, ctx)

@bot.hybrid_command()
async def lottox(ctx):
    await games.play("lottox", state, ctx)

@bot.hybrid_command()
async def states(ctx):
    await games.play("states", state, ctx)



@bot.hybrid_command()
async def lockitin(ctx, pressure: float, id=-1, no_bet=""):
    do_bet = no_bet.lower() not in ["no_bet", "no bet", "nobet"]
    pl = await player.get(state, ctx)
    bb = state.get_barobet(id)
    await bb.guess(pl, pressure, ctx, do_bet=do_bet)

@bot.hybrid_command(name="baroboard")
async def barobet_board(ctx, id=-1):
    bb = state.get_barobet(id)
    await bb.send_guess_board(ctx)

@bot.hybrid_command(name="bbnew")
@is_admin()
async def barobet_new(ctx, day, hour_utc: int, close_date=None, close_hour=None):

    cyclone_dt = parse_day_hour(day, hour_utc)
    if cyclone_dt == None:
        await ctx.send(f"Could not parse cyclone time `{day}`, `{hour_utc}`.")
        return

    if close_date == None or close_hour == None:
        close_dt = None
    else:
        close_dt = parse_day_hour(close_date, int(close_hour))
        if close_dt == None:
            await ctx.send(f"Could not parse close time `{day}`, `{hour_utc}`.")
            return

    await barobets.new_game(cyclone_dt, state, ctx, close_dt=close_dt)

@bot.hybrid_command(name="bbdel")
@is_admin()
async def barobet_delete(ctx, id=-1):
    bb = state.del_barobet(id=id)
    await ctx.send(f"Deleted game {id}")

@bot.hybrid_command(name="bbobs")
@is_admin()
async def barobet_observe(ctx, pressure: float, id=-1):
    bb = state.get_barobet(id)
    await bb.observe_pressure(pressure)

@bot.hybrid_command(name="bbfinish")
@is_admin()
async def barobet_finish(ctx, id=-1):
    bb = state.get_barobet(id)
    await bb.send_rewards(ctx)



def parse_day_hour(day, hour):

    now = dt.datetime.utcnow()

    # example from below
    dates = {
        "sun": 0, # sun: -2 => 5
        "mon": 1, # mon: -1 => 6
        "tue": 2, # tue: 0
        "wed": 3, # wed: 1
        "thu": 4, # thu: 2
        "fri": 5, # fri: 3
        "sat": 6  # sat: 4
    }

    if day.lower() in dates.keys():
        # this is hard for me to think about so I'm gonna use an example
        # let's say it's tuesday the 20th today
        now_wkday = (now.weekday() + 1) % 7 # this becomes 2 (python uses monday = 0 so we add 1)
        this_offset = (dates[day] - now_wkday) % 7 # this rotates the calendar so that 0 is on this day (see above).
        day = now.day + this_offset # this adds the offset to today's day
        # sun => 20 + 5 = 25
        # mon => 20 + 6 = 26
        # tue => 20 + 0 = 20
        # wed => 20 + 1 = 21
        # ....
        print(day)
        return dt.datetime(now.year, now.month, day, hour=hour, tzinfo=dt.timezone.utc)
    else:
        try:
            day_int = int(day)
        except:
            return None
        else:
            return dt.datetime(now.year, now.month, day_int, hour=hour, tzinfo=dt.timezone.utc)



# admin commands ---------------------------------------------------------------


@bot.hybrid_command()
@is_admin()
async def tickets(ctx, action: str, amount: int, user: discord.User):
    p = await player.get_id(state, user.id, ctx)

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
    p = await player.get_id(state, user.id, ctx)
    
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


@bot.hybrid_command()
@is_admin()
async def delete_user(ctx, user: discord.User):
    p = state.players.pop(user.id, None)
    if p != None:
        del p
    await ctx.send(f"Deleted {user.name}")



# run client -------------------------------------------------------------------

state = global_state.load()

with open("data/discord_token.config") as fp:
    token = fp.read()
token = token.strip()

bot.run(token)