import discord
from discord.ext import commands, tasks
from discord.utils import get
from discord.ext.commands import has_permissions, CheckFailure
import asyncio
import time
import os
import random
import datetime
from datetime import date
time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h":3600, "s":1, "m":60, "d":86400}

class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for v, k in matches:
            try:
                time += time_dict[k]*float(v)
            except KeyError:
                raise commands.BadArgument("{} is an invalid time-key! h/m/s/d are valid!".format(k))
            except ValueError:
                raise commands.BadArgument("{} is not a number!".format(v))
        return time



class Button(discord.ui.View):
    def __init__(self,client, *, timeout=180):
        super().__init__(timeout=None)
        self.client = client

    @discord.ui.button(label=f"Entries: 0",custom_id="Entry",style=discord.ButtonStyle.grey,disabled=True) # or .primary
    async def Entry_Button(self,interaction:discord.Interaction,button2: discord.ui.Button):
        pass

    @discord.ui.button(label="Join",custom_id="Joiner",style=discord.ButtonStyle.green,emoji="✅")
    async def Join_Button(self,interaction:discord.Interaction,button: discord.ui.Button):

        cur = await self.client.db.execute("SELECT user_id FROM Giveaway_Entry WHERE message_id = ?", (interaction.message.id,))
        res = await cur.fetchall()

        if res != None:
            for x in res:
                if interaction.user.id == x[0]:
                    return await interaction.response.send_message("You already entered this Giveaway.",ephemeral=True)


        await self.client.db.execute("UPDATE Giveaway_Running SET entries = entries + ? WHERE unique_id = ?", (1,int(interaction.message.id),) )
        await self.client.db.commit()



        cur = await self.client.db.execute("SELECT entries FROM Giveaway_Running WHERE unique_id = ?", (interaction.message.id,))
        res = await cur.fetchone()
        self.children[0].label=f"Entries: {res[0]}"
        await self.client.db.execute("INSERT OR IGNORE INTO Giveaway_Entry (user_id, message_id) VALUES (?,?)", (interaction.user.id, interaction.message.id))
        await self.client.db.commit()
        await interaction.response.edit_message(view=self)





class Giveaway(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def start(self,ctx,GiveawayDuration:TimeConverter = None, winner = None, *,prize):
        hours, remainder = divmod(int(GiveawayDuration), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        embed = discord.Embed(description=f"**{prize}**\n\nWinner: \TBA/\nHosted by: {ctx.author.mention}\n\n♜{days}d:{hours}h:{minutes}m♜", colour=discord.Colour(0x36393e))
        message = await ctx.send(content=":piñata:**__Giveaway Started__**:piñata:",embed=embed,view=Button(self.client))
        await self.client.db.execute("INSERT OR IGNORE INTO Giveaway_Running (unique_id,channel_id,prize,hostedby,total,running,entries,winners) VALUES (?,?,?,?,?,?,?,?)", (message.id,ctx.channel.id,prize,ctx.author.id,GiveawayDuration, 1,0, winner))
        await self.client.db.commit()


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def pause(self,ctx,giveaway_id = None):
        if giveaway_id != None:
            await self.client.db.execute("UPDATE Giveaway_Running SET running = ? WHERE unique_id = ?", (0,int(giveaway_id),) )
            await self.client.db.commit()

            cur = await self.client.db.execute("SELECT unique_id,channel_id,prize,hostedby,total FROM Giveaway_Running WHERE unique_id = ?", (int(giveaway_id),))
            res = await cur.fetchone()

            ch = await self.client.fetch_channel(res[1])
            ms = await ch.fetch_message(res[0])
            user = await self.client.fetch_user(res[3])
            embed = discord.Embed(description=f"**{res[2]}**\n\nWinner: \TBA/\nHosted by: {user.mention}\n\n♜Paused♜", colour=discord.Colour(0x36393e))
            await ms.edit(embed=embed)

            embed = discord.Embed(description=f"**Successfully Paused Giveaway:**\n> <{ms.jump_url}>", colour=discord.Colour(0x36393e))
            await ctx.send(content=":piñata:**__Pausing Giveaways__**:piñata:",embed=embed)


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resume(self,ctx,giveaway_id = None):
        if giveaway_id != None:
            await self.client.db.execute("UPDATE Giveaway_Running SET running = ? WHERE unique_id = ?", (1,int(giveaway_id),) )
            await self.client.db.commit()

            cur = await self.client.db.execute("SELECT unique_id,channel_id,prize,hostedby,total FROM Giveaway_Running WHERE unique_id = ?", (int(giveaway_id),))
            res = await cur.fetchone()

            ch = await self.client.fetch_channel(res[1])
            ms = await ch.fetch_message(res[0])

            embed = discord.Embed(description=f"**Successfully Resumed Giveaway:**\n> <{ms.jump_url}>", colour=discord.Colour(0x36393e))
            await ctx.send(content=":piñata:**__Resuming Giveaways__**:piñata:",embed=embed)




    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reroll(self,ctx,giveaway_id = None):
        if giveaway_id != None:

            cur = await self.client.db.execute("SELECT total FROM Giveaway_Running WHERE unique_id = ?", (int(giveaway_id),))
            res = await cur.fetchone()

            if not res:
                cur = await self.client.db.execute("SELECT user_id FROM Giveaway_Entry WHERE message_id = ?", (int(giveaway_id),))
                res = await cur.fetchall()
                if res:
                    n = random.randint(len(res))
                    winner = await self.client.fetch_user(res[n][0])
                    embed = discord.Embed(description=f"**Successfully Rerolled Giveaway:**\n> {winner.mention}", colour=discord.Colour(0x36393e))
                    await ctx.send(content=":piñata:**__Reroll Giveaways__**:piñata:",embed=embed)





    @commands.command()
    @commands.has_permissions(administrator=True)
    async def running(self,ctx):
        cur = await self.client.db.execute("SELECT unique_id,channel_id,prize,hostedby,total FROM Giveaway_Running WHERE running = ?", (1,))
        res = await cur.fetchall()

        if res:
            Giveaways = ""

            for x in res:
                host = await self.client.fetch_user(x[3])
                Giveaways += f"**{x[2]}** - Hosted By: {host.mention} - Left: {x[4]}s - Running: 1"



            embed = discord.Embed(description=Giveaways, colour=discord.Colour(0x36393e))
        else:
            embed = discord.Embed(description="No Running Giveaways", colour=discord.Colour(0x36393e))

        await ctx.send(content=":piñata:**__Running Giveaways__**:piñata:",embed=embed)

        await self.client.db.commit()


async def setup(client):
    await client.add_cog(Giveaway(client))
    client.add_view(Button(client))
