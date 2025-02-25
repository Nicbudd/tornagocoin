"""Defines the accounts of each of the users/players/participants."""

import datetime as dt
from typing import Optional

import discord
from discord.ext.commands import Context
from discord import Embed

import common as com

TICKET_COST = 20
DAILY_TICKETS = 10
PRESTIGE_NET_WORTH = 100000

class Player:
    """Defines a player of the games.
    Includes their user id and entire inventory
    Use discord library for grabbing information from discord about the user
    (for example, grabbing the username, accent color, etc)"""
    def __init__(self, userid: int, state):
        self.userid = userid

        self.tickets = 20
        self.last_checked = dt.datetime(2000, 1, 1)

        self.coins = 0
        self.stocks = []
        self.prestige = 0

        self.state = state

        state.add_player(userid, self)

    def save(self) -> None:
        """Save the current state of this player to disk.
        Currently just calls .save() on the state."""
        self.state.save()

    async def color(self, ctx: Context) -> Optional[discord.Colour]:
        """Gets user's accent color using discord library"""
        return com.get_user(self.userid, ctx).accent_color

    # TICKETS

    def get_tickets(self) -> int:
        """Gets the amount of tickets the user has (and makes sure it's up to date)"""
        self.refresh_tickets()
        return self.tickets

    def use_tickets(self, count: int) -> bool:
        """Try to take `count` tickets from the player (for payment for a game, for example).
        Returns True if the transaction was successful, False if the user has not enough tickets."""
        self.refresh_tickets()
        if self.tickets >= count:
            self.tickets -= count
            return True
        else:
            return False

    def buy_ticket(self) -> bool:
        """Allows user to pay coins to buy tickets for TICKET_COST price."""
        self.refresh_tickets()
        if self.pay_coins(TICKET_COST):
            self.tickets += 1
            return True
        else:
            return False

    def refresh_tickets(self) -> None:
        """Refresh the amount of tickets the user has, giving them 10 more tickets per day."""
        # if not hasattr(self, "last_checkTICKET_COSTed"):
        #     self.last_checked = dt.datetime(2000, 1, 1)

        if self.last_checked.date() != dt.date.today():
            self.daily_tickets_update()
            self.save()

        self.last_checked = dt.datetime.now()

    def daily_tickets_update(self) -> None:
        """Refreshes the user's balance to have at least DAILY_TICKETS in it."""
        self.tickets = max(self.tickets, DAILY_TICKETS)

    # COINS

    def get_coins(self) -> int:
        """Gets the coin balance of the user"""
        return self.coins

    def add_coins(self, count: int) -> None:
        """Gives the user the specified amount of coins. Also checks if the user has prestiged."""
        self.coins += count
        self.check_prestige()

    # losing in a game doesn't kill your balance entirely
    def lose_coins(self, count: int) -> None:
        """Take the specified amount of coins from the user.
        If the user doesn't have enough coins, set their balance to 0.
        This is used in games where the player loses some amount of coins since
        we don't want to punish players in the early game."""
        count = abs(count)
        if self.coins >= 0:
            if self.coins >= count:
                self.coins -= int(count)
            else:
                self.coins = 0

    def pay_coins(self, count: int) -> bool:
        """Have the user pay the specified amount of coins.
        Returns True if the transaction was successful.
        Returns False if the transaction was unsuccessful
        (because the user does not have enough balance)"""
        if self.coins >= count:
            self.coins -= count
            return True
        else:
            return False

    def check_prestige(self) -> None:
        """Checks if the user has prestiged, and if they have, then let them prestige.
        If the user's net worth goes above PRESTIGE_NET_WORTH, then this function automatically
        sells all of their stocks and coins, and restarts the user from the beginning with a
        prestige trophy."""
        # TODO
        pass


    # STOCKS

    def get_stocks(self):
        """Returns a list of all of the stocks that the user owns."""
        return self.stocks

    def display_stocks(self, ctx: Context) -> None:
        """Displays a detailed list of all stocks in an embed in discord."""
        # TODO
        pass


    # BALANCE

    def net_worth(self) -> int:
        """Gives the net worth of the user, defined as the sum of their coins
        and the value of their stocks."""
        # TODO add sum of stock values
        return self.coins

    def leaderboard_value(self) -> int:
        """Calculates the user's "leaderboard" value, their current net worth and their
        net worth from past prestiges."""
        return self.net_worth() + PRESTIGE_NET_WORTH*self.prestige

    # UTILITIES
    async def send_status(self, ctx: Context) -> None:
        """Sends an embed containing the user's balance, tickets, stocks, etc to discord."""
        user = await self.get_user(ctx)
        em = discord.Embed(color=user.accent_color)

        if user.avatar is None:
            url = None
        else:
            url = user.avatar.url

        em.set_author(name=user.display_name, icon_url=url)
        self.add_status_embed(em, ctx)
        await ctx.send(embed=em)

    def add_status_embed(self, em: Embed, ctx: Context) -> None:
        """Adds statistics about the user to a given embeds"""
        tor = com.tornago(ctx)
        em.add_field(name="Tickets:", value=f"{self.get_tickets()} :tickets:", inline=True)
        em.add_field(name="Coins:", value=f"{self.get_coins()} {tor}", inline=True)
        # TODO: stocks

    async def get_user(self, ctx: Context) -> discord.User:
        """Grabs the user details from the discord client."""
        return await ctx.bot.fetch_user(self.userid)


async def get(state, ctx: Context) -> Player:
    """Finds the author of the message and gets their account.
    If their account doesn't exist, make a new one."""
    return await get_id(state, ctx.author.id, ctx)

async def get_id(state, userid: int, ctx: Context) -> Player:
    """Finds the player's account based on their discord ID.
    If their account doesn't exist, make a new one."""
    if userid in state.players:
        return state.players[userid]
    else:
        player = Player(userid, state)
        await ctx.send(f"Welcome <@{userid}>, an account has been created for you.")
        return player
