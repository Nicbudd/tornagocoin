import datetime as dt
from zoneinfo import ZoneInfo

from common import *

async def new_game(cyclone_dt, state, ctx, close_dt=None):
    g = Game(cyclone_dt, state, ctx, close_dt)
    await ctx.send(f"<@&{GAMER_ROLE}> Guessing for cyclone on **{g.cyclone_dt_str()}** now open.\nGuessing closes **{g.close_dt_str()}**\n*Game #{g.game_id}*.")
    return g

class Game():
    def __init__(self, cyclone_dt, state, ctx, close_dt):
        if close_dt == None:
            # default: closes in 2 days
            self.close_dt = cyclone_dt - dt.timedelta(days=2)
        else:
            self.close_dt = close_dt

        self.cyclone_dt = cyclone_dt
        self.guesses = {}
        self.actual = None
        self.state = state
        self.finished = False

        game_id = state.add_barobet(self)
        self.game_id = game_id

        self.save()

    def save(self):
        self.state.save()

    def close_dt_str(self):
        d = self.close_dt
        eastern = d.astimezone(ZoneInfo("America/New_York"))
        return f"{d.strftime('%a, %b %d @ %HZ')} ({eastern.strftime('%a @ %I %p %Z')})"

    def cyclone_dt_str(self):
        d = self.cyclone_dt
        eastern = d.astimezone(ZoneInfo("America/New_York"))
        return f"{d.strftime('%a, %b %d @ %HZ')} ({eastern.strftime('%a @ %I %p %Z')})"

    async def guess(self, player, pressure, ctx, do_bet=True):

        tor = tornago(ctx)

        userid = player.userid

        now = dt.datetime.now(dt.timezone.utc)
        if now > self.close_dt:
            # don't allow late guesses
            await ctx.send(f"Guessing closed at `{self.close_dt_str()}`")
        
        elif self.finished:
            # don't allow guesses after finished game.
            await ctx.send(f"Game {self.game_id} is closed.")
            await self.send_guess_board(ctx)

        elif not player.pay_coins(100) and do_bet:
            # require to pay 100 coins to play, but only if the player chooses to do a bet.
            await ctx.send(f"Not enough coins to play. Costs 100 {tor}, you are currently at {player.get_coins()} {tornago}.\n You can either earn coins with games in #bot-spam, or add `nobet` after your $lockitin command (and miss out on rewards).")
        
        else:

            # warn user of unusual guess
            if pressure < 960:
                await ctx.send(f"Are you sure? `{pressure:.1f}` seems low.")
            elif pressure > 1040:
                await ctx.send(f"Are you sure? `{pressure:.1f}` seems high.")
            
            # set the guess
            self.guesses[userid] = {"value": pressure, "userid": userid, "do_bet": do_bet, "error": None}
            self.save()

            await ctx.send(f"Confirming `{pressure:.1f}` for {ctx.author.mention} for game #{self.game_id}.")

    def average(self):
        vals = self.guesses.values()

        if len(vals) > 0:
            return sum([x["value"] for x in vals]) / len(vals)
        else:
            return None

    async def observe_pressure(self, pressure):
        self.actual = pressure
        self.save()
        await ctx.send(f"`{pressure}` observed (game {self.game_id})")
    
    async def send_rewards(self, ctx):
        guesses = self.guesses.values()
        if guesses.count == 0:
            await ctx.send("No one made guesses, can't choose winners.")
        elif self.actual != None:

            podiums = self.rankings(self)

            after_text = ""

            # if we were all too high or too low, no one gets it
            if (all([x["value"] > self.actual for x in guesses]) \
                or all([x["value"] < self.actual for x in guesses])) \
                and guesses.count > 1:
                # true if we're all too high, false if we're all to low
                # just grab the first guess and see if it's higher than actual. 
                # if it's lower then all of them are lower, given the above condition
                high = guesses[0]["value"] > self.actual
                high_or_low = "high" if high else "low"
                await ctx.send(f"<@&{GAMER_ROLE}> every player guessed too {high_or_low}. All bets are being kept and nobody gets reward.")
            
            # send to podiums
            else:
                ids = list(podiums)
                rewards = [1500, 1000, 500]
                default_reward = 100

                # add on at least too many default rewards
                # we just don't want the multiplier to go negative
                rewards += [default_reward]*(len(ids))

                for num, winner_id in enumerate(ids):
                    winner = self.state.get_player(winner_id)

                    if guesses[userid]["do_bet"]:
                        winner.add_coins(rewards[num])
                    
                after_text = "\nRewards have been distributed to all players, and coins have been returned."

            # Announce winners
            first_place = get_user(ids[0]).mention

            if guesses.count == 1:
                await ctx.send(f"Congratulations to the sole participant and winner {first_place} for first place!{after_text}")
            elif guesses.count == 2:
                second_place = get_user(ids[1]).mention
                await ctx.send(f"Congratulations to {first_place} for beating {second_place} for first place!{after_text}")
            else:
                second_place = get_user(ids[1]).mention
                third_place = get_user(ids[2]).mention
                await ctx.send(f"Congratulations to {first_place} for first place, as well as {second_place} and {third_place} for a spot on the podium!{after_text}")

            self.finished = True
            self.save()
            await self.send_guess_board(ctx)

        else: # no real-world pressure has been added
            await ctx.send("No real-world pressure has been added.")

    def rankings(self):
        """List all of the users in order by minimum error"""
        # add error to the guess list
        if self.actual == None:
            return None
        else:
            for gamer_id in self.guesses.keys():
                p = self.state.get_player(gamer_id)
                error = self.guesses[gamer_id]["value"] - self.actual
                self.guesses[gamer_id]["error"] = error

            # sort guesses
            ranks = sorted(self.guesses.values(), key=lambda x: abs(x["error"]))

            # return list 
            return ranks

    async def send_guess_board(self, ctx):
        s = ""
        title = ""

        if self.actual == None:
            title = f"Current guesses for game #{self.game_id}"
            s += f"**Average - {self.average():.1f}**\n"
            # sort highest to lowest
            guesses = sorted(self.guesses.values(), key=lambda x: x["value"])
            for g in guesses:
                user = await ctx.bot.fetch_user(g["userid"])
                s += f"{g['value']:.1f} - {user.name}\n"

        else:
            current_final = "Final" if self.finished else "Current"
            title = f"{current_final} results (lowest pressure: {self.actual:.1f})"
            # sort by lowest error
            # display actual guess and error
            guesses = sorted(self.guesses.values(), key=lambda x: abs(x["error"]))
            for g in guesses:
                user = await ctx.bot.fetch_user(g["userid"])
                s += f"{g['value']:.1f} ({g['error']:.1f}) - {user.name}\n"

        em = discord.Embed(title=title, description=s)
        await ctx.send(embed=em)

