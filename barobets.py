""" Implements "BaroBets" discord game.
Users guess the lowest sea level adjusted pressure on a given date for a given location
as a cyclone passes.
Currently requires manually setting the cyclone date, setting observations, and
finishing the game. In the future, that may be able to be automated.
"""
import datetime as dt
import math
from zoneinfo import ZoneInfo
from typing import Optional
from enum import Enum

import discord
from discord.ext.commands import Context

import common as com
from global_state import State
from player import Player

# Warn the user if their guessed pressure is too high or too low
WARN_PRESSURE_TOO_LOW = 960
WARN_PRESSURE_TOO_HIGH = 1040

class Stage(Enum):
    """
    Determines the stage that the game is in.
    """
    OPEN = 0
    CLOSED = 1
    FINISHED = 2
    FORCED_OPEN = 3

class Game():
    """A single BaroBets game."""
    def __init__(self, cyclone_dt: dt.datetime, state: State, close_dt: Optional[dt.datetime]):
        """Do not use! Use new_game() instead as it communicates to the discord client."""
        if close_dt is None:
            # default: closes in 2 days
            self.close_dt: dt.datetime = cyclone_dt - dt.timedelta(days=2)
        else:
            self.close_dt = close_dt

        self.cyclone_dt: dt.datetime = cyclone_dt
        self.guesses: dict[int, Guess] = {}
        self.actual: Optional[float] = None
        self.state: State = state
        self.stage: Stage = Stage.OPEN
        # self.closed: Optional[bool] = None
        # self.finished: bool = False

        game_id = state.add_barobet(self)
        self.game_id = game_id

        self.save()

    def close(self):
        """Closes the game early. Cannot close the game if the game is finished."""
        match self.stage:
            case Stage.OPEN | Stage.CLOSED | Stage.FORCED_OPEN:
                self.stage = Stage.CLOSED
            case Stage.FINISHED:
                # if the game is finished it can't be unfinished.
                pass

    def open(self) -> bool:
        """Forces the guessing to be open"""
        match self.stage:
            case Stage.OPEN | Stage.CLOSED | Stage.FORCED_OPEN:
                self.stage = Stage.FORCED_OPEN
                return True
            case Stage.FINISHED:
                # if the game is finished it can't be unfinished.
                return False

    def update_stage(self):
        """Updates Stage.OPEN if needed."""
        if self.stage == Stage.OPEN:
            now = dt.datetime.now(dt.timezone.utc)
            if now > self.close_dt:
                self.stage = Stage.CLOSED

    def guessing_closed(self) -> bool:
        """Checks if the guessing is closed.
        Finishing the game forces it to be closed no matter what.
        This will also cause the state of the game to change."""
        self.update_stage()

        match self.stage:
            case Stage.FINISHED | Stage.CLOSED:
                return True
            case Stage.FORCED_OPEN | Stage.OPEN:
                return False


    def save(self) -> None:
        """Save the current state of the BaroBets game to disk.
        Currently just calls .save() on the state."""
        self.state.save()

    def close_dt_str(self) -> str:
        """Standard formatting for formatting close_dt into a string."""
        d = self.close_dt
        eastern = d.astimezone(ZoneInfo("America/New_York"))
        return f"{d.strftime('%a, %b %d @ %HZ')} ({eastern.strftime('%a @ %I %p %Z')})"

    def cyclone_dt_str(self) -> str:
        """Standard formatting for formatting cyclone_dt into a string."""
        d = self.cyclone_dt
        eastern = d.astimezone(ZoneInfo("America/New_York"))
        return f"{d.strftime('%a, %b %d @ %HZ')} ({eastern.strftime('%a @ %I %p %Z')})"

    async def guess(self, player: Player, pressure: float,
    ctx: Context, do_bet: bool = True) -> None:
        """Adds a player's guess to the game.
        Players may choose to do_bet, which requires them to pay 100 coins to play.
        In exchange, they may earn more coins back as prizes. If the actual value is
        between two guesses of another player, then all 100 coins are returned."""

        tor = com.tornago(ctx)

        userid = player.userid

        if self.guessing_closed():
            # don't allow guesses after finished game.
            await ctx.send(f"Game {self.game_id} is closed.")
            await self.send_guess_board(ctx)

        # elif not player.pay_coins(100) and do_bet:
        #     # require to pay 100 coins to play, but only if the player chooses to do a bet.


        else:
            try:
                prev_guess = self.guesses[userid]
                prev_guess_bet = prev_guess.did_bet()
            except KeyError:
                prev_guess = None
                prev_guess_bet = False


            # deal with payment

            # if previously we had a bet and we've removed it this time
            if prev_guess_bet and not do_bet:
                await ctx.send(f"Returning your 100 {tor} and removing your bet.")
                prev_guess.made_bet = False
                player.add_coins(100)
            # if previously we didn't have a bet and now we're doing a bet
            elif not prev_guess_bet and do_bet:
                # accept payment
                if not player.pay_coins(100):
                    await ctx.send(f"Not enough coins to play. Costs 100 {tor},"
                    f" you are currently at {player.get_coins()} {tor}.\n-> You can"
                    f" either earn coins with games in #bot-spam, or add `nobet` after"
                    f" your $lockitin command (and miss out on rewards).")
                    return
                # update that we've made the guess
                prev_guess.made_bet = True
            # otherwise do nothing since we haven't changed anything.

            # round the pressure
            pressure = round(pressure*10.0) / 10.0

            # warn user of unusual guess
            if pressure < WARN_PRESSURE_TOO_LOW:
                await ctx.send(f"Are you sure? `{pressure:.1f}` seems low.")
            elif pressure > WARN_PRESSURE_TOO_HIGH:
                await ctx.send(f"Are you sure? `{pressure:.1f}` seems high.")

            # don't allow duplicate guesses
            for g in self.guesses:
                if g.guess() == pressure:
                    p = com.get_user(g.userid, ctx)
                    await ctx.send(f"{p.name} has already made this guess.")

            # set the guess
            self.guesses[userid] = Guess(userid, pressure, do_bet, self)
            self.save()

            await ctx.send(f"Confirming `{pressure:.1f}` for "
            f"{ctx.author.mention} for game #{self.game_id}.")

    def average(self) -> Optional[float]:
        """Calculates the average of all of the guesses."""
        vals = self.guesses.values()

        if len(vals) > 0:
            return sum(x.guess() for x in vals) / len(vals)

        return None

    async def observe_pressure(self, pressure: float, ctx: Context) -> None:
        """Sets the observed pressure for this game (only if the game is closed).
        Confirms with user that the pressure has been observed.
        Also saves the game."""
        self.update_stage()

        match self.stage:
            case Stage.CLOSED:
                self.actual = pressure
                self.save()
                await ctx.send(f"`{pressure:.2f}` observed (game #{self.game_id})")
            case Stage.FORCED_OPEN | Stage.OPEN:
                await ctx.send("The game is currently open. The pressure cannot be observed until "
                "the game is closed.")
            case Stage.FINISHED:
                await ctx.send("The game is finished. The pressure cannot be observed "
                "after the game has finished.")


    async def send_rewards(self, ctx: Context) -> None:  # noqa: PLR0912
        """Finishes the game and sends rewards to all players"""
        match self.stage:
            case Stage.FINISHED:
                await ctx.send(f"Game #{self.game_id} is already finished.")
                return

            case Stage.OPEN | Stage.FORCED_OPEN:
                await ctx.send(f"Game #{self.game_id} has not been closed yet. "
                "The game cannot be finished until it is closed and an observation provided.")
                return

            case Stage.CLOSED:
                guesses = self.guesses.values()

                if len(guesses) == 0:
                    await ctx.send("No one made guesses, can't choose winners.")

                elif self.actual is None: # no real-world pressure has been added
                    await ctx.send("No real-world pressure has been observed/added.")

                else:

                    podiums = self.rankings()

                    after_text = ""

                    # if we were all too high or too low, no one gets it
                    if (all(x.guess() > self.actual for x in guesses) \
                        or all(x.guess() < self.actual for x in guesses)) \
                        and len(guesses) > 1:
                        # true if we're all too high, false if we're all to low
                        # just grab the first guess and see if it's higher than actual.
                        # if it's lower then all of them are lower, given the above condition
                        a_guess = list(self.guesses.values())[0]
                        high = a_guess.guess() > self.actual
                        high_or_low = "high" if high else "low"
                        await ctx.send(f"<@&{com.GAMER_ROLE}> every player guessed "
                        f"too {high_or_low}. All bets are being kept and nobody gets reward.")

                    # send to podiums
                    else:
                        ids = list(podiums or [])
                        rewards = [1500, 1000, 500]
                        default_reward = 100

                        # add on at least too many default rewards
                        # we just don't want the multiplier to go negative
                        rewards += [default_reward]*(len(ids)) + 100

                        for num, winner_id in enumerate(ids):
                            winner = self.state.get_player(winner_id)

                            if self.guesses[winner_id].did_bet():
                                winner.add_coins(rewards[num])

                        after_text = ("\nRewards have been distributed to all players,"
                        " and coins have been returned.")

                    # Announce winners
                    first_place = await com.get_user(ids[0], ctx)

                    if len(guesses) == 1:
                        await ctx.send("Congratulations to the sole participant and winner"
                        f" {first_place.mention} for first place!{after_text}")
                    elif len(guesses) == 2: # noqa: PLR2004
                        second_place = await com.get_user(ids[1], ctx)
                        await ctx.send(f"Congratulations to {first_place.mention} for beating"
                        f" {second_place.mention} for first place!{after_text}")
                    else:
                        second_place = await com.get_user(ids[1], ctx)
                        third_place = await com.get_user(ids[2], ctx)
                        await ctx.send(f"Congratulations to {first_place.mention} for first place, "
                        f"as well as {second_place.mention} and {third_place.mention} for a spot "
                        f"on the podium!{after_text}")

                    self.stage = Stage.FINISHED
                    self.save()
                    await self.send_guess_board(ctx)

    def rankings(self) -> Optional[list[int]]:
        """List all of the users in order by minimum error"""
        # add error to the guess list
        if self.actual is None:
            return None
        # sort guesses
        ranks = sorted(self.guesses.values(), key=lambda x: abs(x.error() or 0))
        # x.error() or 0 is fine, the 0 is arbitrary, we already check that self.actual
        # isn't None

        # return list
        return [r.get_userid() for r in ranks]

    async def send_guess_board(self, ctx: Context):
        """
        Using the discord context, send the list of guesses.
        If no observed value has been given, it lists the pressure guesses from low to high.
        If the , it lists the guesses from best to worst
        """
        s = ""
        title = ""

        if self.actual is None:
            title = f"Current guesses for game #{self.game_id}"
            s += f"**Average - {self.average():.1f}**\n"

            # sort by guesses highest to lowest
            guesses = sorted(self.guesses.values(), key=lambda x: x.guess())
            for g in guesses:
                user = await ctx.bot.fetch_user(g.get_userid())
                s += f"{g.guess():.1f} - {user.name}\n"

        else:
            current_final = "Final" if self.stage == Stage.FINISHED else "Current"
            title = f"{current_final} results (lowest pressure: {self.actual:.1f})"
            # sort by lowest error
            # display actual guess and error
            # print(self.guesses.values())
            guesses = sorted(self.guesses.values(), key=lambda x: abs(x.error() or math.inf))
            for g in guesses:
                user = await ctx.bot.fetch_user(g.get_userid())
                s += f"{g.guess():.1f} ({g.error():.1f}) - {user.name}\n"

        em = discord.Embed(title=title, description=s)
        await ctx.send(embed=em)


async def new_game(cyclone_dt: dt.datetime, state: State,
ctx: Context, close_dt: Optional[dt.datetime] = None) -> Game:
    """
    Initiates a new game. Requires the cyclone date and time,
    as well as the time when guessing closes.
    """
    g = Game(cyclone_dt, state, close_dt)
    await ctx.send(
        f"<@&{com.GAMER_ROLE}> Guessing for cyclone on **{g.cyclone_dt_str()}**"
        f" now open.\nGuessing closes **{g.close_dt_str()}**\nGame #{g.game_id}."
    )
    return g


class Guess():
    """A guess for the betting game"""
    def __init__(self, userid: int, pressure: float, do_bet: bool, game: Game):
        self.made_bet = do_bet
        self.pressure = pressure
        self.userid = userid
        self.game = game
        # self.error: Optional[float] = None

    def save(self):
        """Saves the guess. Does this by saving the game."""
        self.game.save()

    def guess(self) -> float:
        """Get the value of the guess"""
        return self.pressure

    def get_userid(self) -> int:
        """Returns the userid"""
        return self.userid

    def change_guess(self, pressure: float) -> None:
        """Change the pressure guess of this guess. May end up being unused."""
        self.pressure = pressure

    def error(self) -> Optional[float]:
        """Compare the observed result to the guess to get the error."""
        if self.game.actual is None:
            return None
        return self.pressure - self.game.actual

    def did_bet(self) -> bool:
        """Returns the value of do_bet. Whether the user chose to make a bet."""
        return self.made_bet
