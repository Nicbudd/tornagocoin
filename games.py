from common import *
import random
import discord
import player as pl

async def play(game_name, state, ctx, testplay=False):
    player = await pl.get(state, ctx)

    game_name = game_name.lower()
    result = get_result(game_name)

    if result == None:
        ctx.send(f"Unknown game `{game_name}`")
    else:

        if testplay:
            paid = False
        else:
            paid = await collect_tickets(result["cost"], player, ctx)

        if paid or testplay:
            await confirm_result(result, player, ctx, paid)


async def collect_tickets(ticket_cost, player, ctx):
    if player.use_tickets(ticket_cost):
        return True
    else:
        await ctx.send(f"Not enough :tickets: to play. This game requires {ticket_cost} :tickets: to play, you have {player.get_tickets()}.\nRun the command `testplay` to see what to expect from the game.")
        return False


async def confirm_result(result, player, ctx, paid):
    coins = result["coins"]

    if paid:
        # adjust the player's balance
        if coins < 0:
            player.lose_coins(coins)
        else:
            player.add_coins(coins)

        # save state
        player.save()


    # embed
    user = await player.get_user(ctx)
    em = discord.Embed(color=user.accent_color)
    em.set_author(name=result["name"])
    em.description = f"*{result['description']}*"
    
    text = result["text"]
    if coins < 0:
        text += f"\n(Lost {coins} {tornago(ctx)})"
    else:
        text += f"\n(Won {coins} {tornago(ctx)})"
    
    em.add_field(name=result["outcome"], value=text, inline=False)
    if paid:
        # em.add_field(name=ctx.author.display_name, value="", inline=False)
        player.add_status_embed(em, ctx)
    

    await ctx.send(embed=em)


def get_result(game):

    if "lazy" in game or "eight" in game or game in ["l8", "8"]:
        return lazy_eights()
    elif game in ["d6", "dice", "die"]:
        return d6()
    elif game in ["d20"]:
        return d20()
    elif game in ["lotto", "lottery"]:
        return lotto()
    elif game in ["lotto_x", "lotto_ex", "lotto_extreme", "lotto_xtreme", "lottox", "lottoex", "lottoextreme", "lottoxtreme"]:
        return lotto_xtreme()
    elif game in ["state", "states", "ohio", "oh"]:
        return states_game()
    else:
        return None




# games ------------------------------------------------------------------------

def lazy_eights():
    
    result = {
        "name": "Lazy Eights",
        "description": "Oh, so you're boring?",
        "cost": 1,
        "outcome": "Win",
        "text": "Shocking. You won.",
        "coins": 8,
    }

    return result


def d6():

    roll = random.randint(1, 6)

    outcome = f"Roll: {roll}"
    text = ""
    coins = (roll - 1) * 4

    result = {
        "name": "d6",
        "description": "As simple as it gets.",
        "cost": 1,
        "outcome": outcome,
        "text": text,
        "coins": coins,
    }

    return result


def d20():

    roll = random.randint(1, 20)

    outcome = f"Roll: {roll}"
    
    if roll == 20:
        text = "NATURAL 20!"
        coins = 200
    else:
        text = ""
        coins = 0
    
    result = {
        "name": "d20",
        "description": "C'mon, nat 20...",
        "cost": 1,
        "outcome": outcome,
        "text": text,
        "coins": coins,
    }

    return result


def lotto():

    roll = random.randint(1, 1000)

    if roll == 1:
        outcome = "JACKPOT!!!"
        text = ""
        coins = 9000,
    elif roll <= 100:
        outcome = "Win"
        text = "You won a minor prize!"
        coins = 20
    else:
        outcome = "Try Again"
        text = "Better luck next time!"
        coins = 0

    result = {
        "name": "Lotto",
        "description": "Jackpot or Bust!",
        "cost": 1,
        "outcome": outcome,
        "text": text,
        "coins": coins,
    }

    return result



def lotto_xtreme():

    roll = random.randint(1, 10000)

    if roll == 1:
        outcome = "JACKPOT!!!!!"
        text = ""
        coins = 50000,
    elif roll <= 10:
        outcome = "Mega Win!"
        text = ""
        coins = 5000
    elif roll <= 100:
        outcome = "Big Win"
        text = ""
        coins = 50
    elif roll <= 600:
        outcome = "Win"
        text = "You won a minor prize!"
        coins = 10
    else:
        outcome = "Try Again"
        text = "Better luck next time!"
        coins = 0

    result = {
        "name": "Lotto XTREME",
        "description": "XTREME JACKPOT POTENTIAL",
        "cost": 1,
        "outcome": outcome,
        "text": text,
        "coins": coins,
    }

    return result


states = ["Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming"]

def states_game():

    state = states[random.randint(0, 49)]

    outcome = state

    if state == "New Hampshire":
        text = "Based."
        coins = 200,
    elif state == "Ohio":
        text = "Looks like you're going to the shadow realm, Jimbo"
        coins = -950
    else:
        text = ""
        coins = 25

    result = {
        "name": "State Roulette",
        "description": "Don't get Ohio!",
        "cost": 1,
        "outcome": outcome,
        "text": text,
        "coins": coins,
    }

    return result


