from common import *
import random
import discord


async def play(game_name, player, ctx, testplay=False):
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
    color = await author_color(ctx)
    em = discord.Embed(color=color)
    em.set_author(name=result["name"])
    em.description = f"*{result['description']}*"
    
    text = result["text"]
    if coins < 0:
        text += f"\n(Lost {coins} {tornago(ctx)})"
    else:
        text += f"\n(Won {coins} {tornago(ctx)})"
    
    em.add_field(name=result["outcome"], value=result["text"], inline=False)
    if paid:
        em.add_field(name=ctx.author.display_name, value="", inline=False)
        player.add_status_embed(em, ctx)
    

    await ctx.send(embed=em)


def get_result(game):

    if "lazy" in game or "eight" in game or game in ["l8", "8"]:
        return lazy_eights()
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


