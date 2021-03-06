from discord.ext import commands
from pbtahelpers import *


def setup(bot):
    characterfile = 'bbcharacters.json'
    movefile = 'bbmoves.json'
    bot.add_cog(PBTA(bot,characterfile,movefile))


class PBTA(commands.Cog):
    def __init__(self,bot,characterfile,movefile):
        self.bot = bot
        self.characterfile = characterfile
        self.movefile = movefile
        self.chardata,self.movedata,self.allstats = loadvarsfromfiles(characterfile,movefile)
        

    # roll based on character sheet or roll with a modifier depending on user input
    @commands.command(name='r', help='Roll 2d6 plus a stat or numeric modifier',description='Roll 2d6 plus a stat or numeric modifier. By default, use the character your Discord user is associated with, or specify a specific character.\n Usage: .r [number or name of stat] [*character]')
    async def botroll(self, ctx, modifier=None, character="user"):
        
        character = matchabbr(character,self.chardata)
        charinfo,response = botgetcharinfo(str(ctx.message.author),character,self.chardata)
        
        if not response:
            response = botrollgeneric(modifier,charinfo)

        await ctx.send(f'{ctx.message.author.mention}: {response}')

    @commands.command(name='m', help='Do a specific move',description='By default, use the character your Discord user is associated with, or specify a character to roll for.\n Usage: .m [name of move or abbreviation] [*character]')
    async def rollformove(self,ctx,move=None,modifier='0',advantage='none',character="user"): 

        character = matchabbr(character,self.chardata)
        charinfo,response = botgetcharinfo(str(ctx.message.author),character,self.chardata)                

        if response:
            await ctx.send(f'{ctx.message.author.mention}: {response}')
        else:

            # find moves that are specific to a character
            cmovedata = addcharmoves(charinfo,self.movedata)
            if move:
                move = matchabbr(move,cmovedata)

            if move not in cmovedata:
                response = 'Invalid move, try again.'
            else:

                # roll the move with appropriate modifiers
                moveinfo = cmovedata[move]
                response = botcharmove(moveinfo,charinfo,modifier)
                    
            await ctx.send(f'{ctx.message.author.mention}: {response}')

    @commands.command(name='list', help='List all moves, characters, or specific character stats',description='Type m to see moves, c to see characters, or a character\'s name to see their stats.')
    async def liststuff(self,ctx,listtype='m'):
        
        responselist = [f'{ctx.message.author.mention}:']
        listtype = matchabbr(listtype,['moves','characters'])

        if listtype in ['m','move','moves']:
            responselist.extend(self.listmovedata())
        
        elif listtype in ['c','character','char','chars','characters']:
            for char in self.chardata:
                responselist.extend(self.listchardata(char))
                responselist.append("")
        
        else:
            # if moves or characters aren't specified, list a specific character's full stats
            charname = matchabbr(listtype,self.chardata)
            if charname in self.chardata:
                responselist.extend(self.listchardata(charname))
            else:
                responselist[0] = responselist[0] + " Invalid input. Type m (or moves) to see moves, c (or characters) to see characters, or a character's name to see their stats."

        response = "\n".join(responselist)
        await ctx.send(response)

    def listmovedata(self):
        responselist = []

        responselist.append("*Basic Moves*")
        # basic moves
        for move in self.movedata:
            responselist.append(
                f'**{self.movedata.get(move).get("name")}**: {self.movedata.get(move).get("description")}'
            )

        # custom character moves
        responselist.append("\n*Character-Specific Moves*")
        for character in self.chardata:
            if self.chardata.get(character).get("custom moves"):
                for cmove in self.chardata.get(character).get("custom moves").values():
                    responselist.append(
                        f'**{cmove.get("name")}** ({self.chardata.get(character).get("character name")}): {cmove.get("description")}'
                    )
        if responselist[-1] == "\n*Character-Specific Moves*":
            responselist.pop()

        return responselist

    def listchardata(self,charname):
        responselist = []
        
        for key,value in self.chardata.get(charname).items():
            if key == "stats":
                statstr = '**Stats:** '
                for key, value in self.chardata.get(charname).get("stats").items():
                    statstr = statstr + f'{key.title()} {value}, '
                responselist.append(statstr[:-2])
            elif key == "custom moves":
                movestr = '**Custom Moves:** '
                for cmove in value.values():
                    movestr = movestr + f'\n - {cmove.get("name")}: {cmove.get("description")}'
                responselist.append(movestr)
            else:
                responselist.append(
                    f'**{key.title()}**: {value}'
                )
        return responselist

    @commands.command(name='update', hidden=True,help='Update a value on a character\'s sheet',description='Update a value on a character\'s sheet. This can be overwritten unless saved using the save command. \n Usage: .set fluid 3 katara')
    async def outputlist(self,ctx,key=None,newval=None,character='user'):
        if not newval or not key:
            response = 'Invalid input, try again. Example syntax: .update fluid 3 katara.'
        else:
            character = matchabbr(character,self.chardata)
            charinfo,response = botgetcharinfo(str(ctx.message.author),character,self.chardata)

        
        if response:
            await ctx.send(f'{ctx.message.author.mention}: {response}')
        else:
            if key in charinfo:
                if charinfo[key] != newval:
                    response = f"{ctx.message.author.mention}: {charinfo.get('character name')}\\'s {key.title()} has been changed from {charinfo[key]} to {newval}."
                    charinfo[key] = newval
                else:
                    response = f"{ctx.message.author.mention}: {charinfo.get('character name')}\\'s {key.title()} is already equal to {charinfo[key]}. No changes made."
            else:
                stat = matchabbr(key,self.allstats)
                if stat in self.allstats:
                    newstat = checkvalidstat(newval)
                    if not newstat and newstat != 0:
                        response = f'{ctx.message.author.mention}: Invalid input, try again. Stats can only be set to a maximum of +3.'
                    elif charinfo['stats'][stat] != newstat:
                        response = f"{ctx.message.author.mention}: {charinfo.get('character name')}\\'s {stat.title()} stat has been changed from {charinfo['stats'][stat]} to {newstat}."
                        charinfo['stats'][stat] = newstat
                    else:
                        response = f"{ctx.message.author.mention}: {charinfo.get('character name')}\\'s {stat.title()} stat is already equal to {newstat}. No changes made."
                else:
                    response = f'{ctx.message.author.mention}: Invalid input, try again. Example syntax: .update fluid 3 katara'

            await ctx.send(response)


    @commands.command(name='save', hidden=True,help='Save all current character stats to file',description='Stats will be overrwritten on bot restart, unless saved using this command.')
    async def savetofile(self, ctx):

        response = f'{ctx.message.author.mention}: ' + savechardata(self.chardata,self.characterfile)

        await ctx.send(response)

