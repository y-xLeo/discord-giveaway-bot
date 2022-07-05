import discord
import asyncio
import os
import urllib.parse, urllib.request, re
import aiofiles
from discord.ext import commands, tasks
from discord.utils import get
from discord.ext.commands import has_permissions, CheckFailure
import random
import aiosqlite
import time



client = commands.Bot(command_prefix="$", intents=discord.Intents.all())

@client.event
async def on_ready():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")
            print("Cog Loaded!")
    print(f'{client.user} has connected to Discord!')
    client.db = await aiosqlite.connect("Database.db") # money table, open giveaways table, entries table
    await client.db.execute("CREATE TABLE IF NOT EXISTS Giveaway_Entry (user_id int, message_id int)")
    await client.db.execute("CREATE TABLE IF NOT EXISTS Giveaway_Running (unique_id int,channel_id int,prize string, hostedby int,total float, running int,entries int,winners int, PRIMARY KEY (unique_id))")
    Giveaway_Updater.start()




@tasks.loop(seconds=10)
async def Giveaway_Updater():
    cur = await client.db.execute("SELECT unique_id,channel_id,prize,hostedby,total,winners FROM Giveaway_Running WHERE running = ?", (1,))
    res = await cur.fetchall()
    if res != None:
        for x in res:
            channel = await client.fetch_channel(x[1])
            message = await channel.fetch_message(x[0])

            user = await client.fetch_user(x[3])

            hours, remainder = divmod(int(x[4]-10), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)

            if x[4]-10 <= 0:
                cur = await client.db.execute("SELECT user_id FROM Giveaway_Entry WHERE message_id = ?", (x[0],))
                res = await cur.fetchall()
                if res:
                    list = []
                    for l in res:
                        y = str(l[0])
                        list.append(y)
                    winners = ""
                    if len(list) < x[5]:
                        for i in range(len(list)):
                            n = random.choice(list)
                            list.remove(n)
                            winner = await client.fetch_user(int(n))
                            winners += f"{winner.mention}\n"

                    else:
                        for i in range(x[5]):
                            n = random.choice(list)
                            list.remove(n)
                            winner = await client.fetch_user(int(n))
                            winners += f"{winner.mention}\n"




                    embed = discord.Embed(description=f"**{x[2]}**\n\nWinner: \n{winners}\nHosted by: {user.mention}\n\n♜Ended♜", colour=discord.Colour(0x36393e))
                    await message.edit(content=":piñata:**__Giveaway Ended__**:piñata:",embed=embed)
                    await client.db.execute("DELETE FROM Giveaway_Running WHERE unique_id = ?", (x[0],))
                    return
                else:
                    embed = discord.Embed(description=f"**{x[2]}**\n\nWinner: Not enough Entries.\nHosted by: {user.mention}\n\n♜Ended♜", colour=discord.Colour(0x36393e))
                    await message.edit(content=":piñata:**__Giveaway Ended__**:piñata:",embed=embed)
                    await client.db.execute("DELETE FROM Giveaway_Running WHERE unique_id = ?", (x[0],))
                    return

            if x[4]-10 <= 60:
                embed = discord.Embed(description=f"**{x[2]}**\n\nWinner: \TBA/\nHosted by: {user.mention}\n\n♜{seconds}s♜", colour=discord.Colour(0x36393e))
                await message.edit(embed=embed)
            else:


                embed = discord.Embed(description=f"**{x[2]}**\n\nWinner: \TBA/\nHosted by: {user.mention}\n\n♜{days}d:{hours}h:{minutes}m♜", colour=discord.Colour(0x36393e))
                await message.edit(embed=embed)


            await client.db.execute("UPDATE Giveaway_Running SET total = total - 10 WHERE unique_id = ?", (x[0],))


    await client.db.commit()


client.run(token)
