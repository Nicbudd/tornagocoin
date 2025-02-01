import json
from common import *

async def get(state, ctx):
    return await get_id(state, ctx.author.id, ctx)

async def get_id(state, userid, ctx):
    if userid in state.players:
        return state.players[userid]
    else:
        player = Player(userid, state)
        await ctx.send(f"Welcome <@{userid}>, an account has been created for you.")
        return player


class Player:
    def __init__(self, userid, state):
        self.userid = userid
        self.tickets = 10
        self.coins = 0
        self.stocks = []
        self.state = state

        state.add_player(userid, self)

    def save(self):
        self.state.save()

    async def color(self, ctx):
        color(ctx)

    # TICKETS

    def get_tickets(self):
        return self.tickets

    def use_tickets(self, count):
        if self.tickets >= count:
            self.tickets -= count
            return True
        else:
            return False

    def buy_ticket(self):
        if self.pay_coins(20):
            self.tickets += 1
            return True
        else:
            return False


    # COINS

    def get_coins(self):
        return self.coins

    def add_coins(self, count):
        self.coins += int(count)
        self.check_prestige()

    # losing in a game doesn't kill your balance entirely
    def lose_coins(self, count):
        if self.coins >= 0:
            if self.coins >= count:
                self.coins -= int(count)
            else:
                self.coins = 0

    def pay_coins(self, count):
        if self.coins >= count:
            self.coins -= int(count)
            return True
        else:
            return False

    def check_prestige(self):
        # TODO
        pass


    # STOCKS

    def get_stocks(self):
        return self.data["stocks"]

    def display_stocks(self):
        # TODO
        pass


    # UTILITIES
    async def send_status(self, ctx):
        color = await author_color(ctx)
        em = discord.Embed(color=color)
        em.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        self.add_status_embed(em, ctx)
        await ctx.send(embed=em)

    def add_status_embed(self, em, ctx):
        em.add_field(name="Tickets:", value=f"{self.get_tickets()} :tickets:", inline=True)
        em.add_field(name="Coins:", value=f"{self.get_coins()} {tornago(ctx)}", inline=True)


