from logging import exception
import os
import nextcord as discord
import string
import random
import asyncio
import shutil
import time
import json
import requests
import pymysql
import re
from datetime import datetime
from nextcord.ext import commands
from dotenv import load_dotenv, find_dotenv
from os import path

intents = discord.Intents().all()
intents.members = True
load_dotenv(find_dotenv())
bot_token = os.environ.get("bot_token")
prefix = os.environ.get("prefix")
mysql_ip = os.environ.get("mysql_ip")
mysql_port = os.environ.get("mysql_port")
mysql_database = os.environ.get("mysql_database")
mysql_user = os.environ.get("mysql_user")
mysql_pass = os.environ.get("mysql_pass")
web_api_key = os.environ.get("web_api_key")
cloudflare_email = os.environ.get("cloudflare_email")
cloudflare_api_key = os.environ.get("cloudflare_api_key")
client = commands.Bot(command_prefix = prefix, help_command=None, intents=intents)

connection = None
try:
    connection = pymysql.connect(host=mysql_ip,
                                 database=mysql_database,
                                 user=mysql_user,
                                 port = int(mysql_port),
                                 password=mysql_pass,
                                 autocommit=True)
    print("Connected to the DB!")
except:
    print("Couldn't connect to the database.")
    exit()

if connection is None:
    exit()

cursor = connection.cursor()

currently_creating = []
in_setup = []
in_setup_gdpsbrowser = []
donator_roles = [743031850435477594, #Perms
                 743031374251950131, #Admin
                 746663126338109581, #Developer
                 789529083372634183, #Super Moderator
                 767099706861027429, #VIP
                 764639361999962143, #Patreon Level 6
                 764639282857246800, #Patreon Level 5
                 764639157661597756, #Patreon Level 4
                 764639093207597066, #Patreon Level 3
                 764638878320689183, #Patreon Level 2
                 743031628212994130, #Patreon Level 1
                 803894379982880778, #Donator
                 763337908211154955, #Server Booster
                 863465353437904906, #Server Booster (GDPSFH RU)
                 832310593657896970] #Big gdps owner

@client.command()
async def c(ctx):
    print(f"command ps!c used by {ctx.author.id}")
    language = checklang(ctx.guild.id)
    if language is False:
        await ctx.send("An error occured with the language selector.")
        return
    lang = language[0]
    server_config = language[1]
    cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [ctx.author.id])
    data = cursor.fetchall()
    allowed_channels = [797900335070183474, #test-bot - GDPSFH
                        748238238736711761, #create-gdps - GDPSFH
                        863435775197839369] #create-gdps - GDPSFH RU
    cursor = execute_sql("select lockdown_status from gdps_creator_config where id = %s", [server_config])
    lockdown_status = cursor.fetchall()
    if lockdown_status[0][0] == 1:
        puser = is_admin(ctx.author.id, server_config)
        if puser is not True:
            embed = discord.Embed(title=getlang(f"{lang}_ccmd_lockdown_enabled"), description=getlang(f"{lang}_ccmd_lockdown_enabled_description"), color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
    if ctx.channel.id not in allowed_channels:
        embed = discord.Embed(description=getlang(f"{lang}_ccmd_only_in_creategdps_channel"), color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    if ctx.author.id in currently_creating:
        embed = discord.Embed(title=getlang(f"{lang}_ccmd_finish_setup"), color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    check_has_gdps = has_gdps(ctx.author.id)
    if check_has_gdps == True:
        if data[0][5] == 1:
            embed = discord.Embed(title=getlang(f"{lang}_ccmd_banned_creating_gdps"), color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        else:
            embed = discord.Embed(title=getlang(f"{lang}_ccmd_already_has_gdps"), color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
    else:
        try:
            valid_versions = ["2.1"]

            def check(m):
                return m.author == ctx.message.author and m.guild is None

            first_msg = discord.Embed(title=getlang(f"{lang}_ccmd_provide_us_information"), description=getlang(f"{lang}_ccmd_provide_gdps_name"), color = discord.Colour.green())
            await ctx.author.send(embed=first_msg)
            currently_creating.append(ctx.author.id)
            embed = discord.Embed(title=getlang(f"{lang}_ccmd_gdps_setup_begun"), color = discord.Colour.green())
            await ctx.send(embed=embed)
            while True:
                gdps_name = await client.wait_for('message', check=check)
                result = re.match(r"^[a-zA-Z0-9]{1,20}$", gdps_name.content)
                if result:
                    break
                else:
                    embed = discord.Embed(title="This name is invalid, please only use letters, numbers, no spaces and a maximum of 20 characters.", color = discord.Colour.red())
                    await ctx.author.send(embed=embed)

            embed = discord.Embed(title=getlang(f"{lang}_ccmd_gdps_custom_url_title"), description=getlang(f"{lang}_ccmd_gdps_custom_url_description"), color = discord.Colour.green())
            await ctx.author.send(embed=embed)
            name_exist_error = discord.Embed(title=getlang(f"{lang}_ccmd_gdps_custom_url_exist_error"), color = discord.Colour.red())
            while True:
                gdps_custom_url = await client.wait_for('message', check=check)
                result = re.match(r"^[a-zA-Z0-9]{12}$", gdps_custom_url.content)
                if result:
                    cursor = execute_sql("select null from gdps_creator_userdata where gdps_custom_url = %s", [gdps_custom_url.content])
                    if cursor.rowcount > 0:
                        await ctx.author.send(embed=name_exist_error)
                    else:
                        break
                else:
                    embed = discord.Embed(title="This custom url is invalid, please only use letters, numbers, no spaces and a maximum of 12 characters.", color = discord.Colour.red())
                    await ctx.author.send(embed=embed)

            embed = discord.Embed(title=getlang(f"{lang}_ccmd_gdps_version"), color = discord.Colour.green())
            await ctx.author.send(embed=embed)
            while True:
                gdps_version = await client.wait_for('message', check=check)
                result = re.match(r"^[0-9]{1}.[0-9]{1}$", gdps_version.content)
                if gdps_version.content in valid_versions and result:
                    break
                embed = discord.Embed(title=getlang(f"{lang}_ccmd_gdps_version_invalid_error"), color = discord.Colour.red())
                await ctx.author.send(embed=embed)

            printable = f'{string.ascii_letters}{string.digits}'
            printable = list(printable)
            random.shuffle(printable)
            random_password = random.choices(printable, k=22)
            password = ''.join(random_password)
            userid = ctx.author.id

            in_setup.append(ctx.author.id)
            cursor = execute_sql("insert into gdps_creator_userdata (userID, gdps_name, gdps_custom_url, gdps_version, gdps_password, left_server, moderators, on_gdps_browser, created_in) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)", [int(userid), gdps_name.content, gdps_custom_url.content, gdps_version.content, password, 0, "[]", 0, server_config])

            embed = discord.Embed(title="<a:loading:762295133747413022> " + getlang(f"{lang}_ccmd_creating_gdps"), color = discord.Colour.green())
            creating = await ctx.author.send(embed=embed)

            f = open("/etc/apache2/sites-available/gdps.conf", "r")
            contents = f.readlines()
            f.close()

            value = f"    <Directory \"/var/www/gdps/{str(gdps_custom_url.content)}/\">\n        ProxyFCGISetEnvIf \"true\" PHP_ADMIN_VALUE \"open_basedir=/var/www/gdps/{str(gdps_custom_url.content)}/:/usr/share/phpmyadmin/:/usr/share/php\"\n    </Directory>\n\n"

            contents.insert(5, value)

            f = open("/etc/apache2/sites-available/gdps.conf", "w")
            contents = "".join(contents)
            f.write(contents)
            f.close()
            process = await asyncio.create_subprocess_shell(f'./CreateGDPS-Bot.sh {str(gdps_name.content)} {str(gdps_version.content)} {str(gdps_custom_url.content)} {str(password)}')
            await process.communicate()
            process = await asyncio.create_subprocess_shell('service apache2 reload')
            await process.communicate()

            await creating.delete()
            in_setup.remove(ctx.author.id)
            currently_creating.remove(ctx.message.author.id)

            embed = discord.Embed(title=getlang(f"{lang}_ccmd_final_embed_title"), description=f"<@{userid}>", color = discord.Colour.green())
            embed.add_field(name=getlang(f"{lang}_ccmd_final_embed_mysql_link"), value="http://ps.fhgdps.com/phpmyadmin/", inline=False)
            embed.add_field(name=getlang(f"{lang}_ccmd_final_embed_mysql_user"), value=f"```gdps_{gdps_custom_url.content}```", inline=True)
            embed.add_field(name=getlang(f"{lang}_ccmd_final_embed_mysql_password"), value=f"```{password}```", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(name=getlang(f"{lang}_ccmd_final_embed_ftp_ip"), value=f"```ftp.fhgdps.com```", inline=True)
            embed.add_field(name=getlang(f"{lang}_ccmd_final_embed_ftp_port"), value=f"```21```", inline=True)
            embed.add_field(name=getlang(f"{lang}_ccmd_final_embed_ftp_user"), value=f"```gdps_{gdps_custom_url.content}```", inline=False)
            embed.add_field(name=getlang(f"{lang}_ccmd_final_embed_ftp_password"), value=f"```{password}```", inline=False)
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(name=getlang(f"{lang}_ccmd_final_embed_main_website"), value=f"http://ps.fhgdps.com/{gdps_custom_url.content}", inline=False)
            embed.add_field(name=getlang(f"{lang}_ccmd_final_embed_tools_page"), value=f"http://ps.fhgdps.com/{gdps_custom_url.content}/tools")
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(name=getlang(f"{lang}_ccmd_final_embed_optional_bot_title"), value=getlang(f"{lang}_ccmd_final_embed_optional_bot_description"))
            await ctx.author.send(embed=embed)

            embed = discord.Embed(title="Warning", description=f"The download links provided below are **temporary** and will be deleted in 20 minutes. You should download both version and re-upload these somewhere else (Dropbox, Mega.nz, ...) and share it as the main download link for other people to download and play on your GDPS. \nYou can re-download those at any time using `ps!getdownload`. \n\nPC: [Download](http://ps.fhgdps.com/{gdps_custom_url.content}/download/{gdps_name.content}.zip) \nMobile: [Download](http://ps.fhgdps.com/{gdps_custom_url.content}/download/{gdps_name.content}.apk)", color = discord.Colour.orange())
            await ctx.author.send(embed=embed)
            await asyncio.sleep(1200)
            shutil.rmtree(f"/var/www/gdps/{gdps_custom_url.content}/download/")
            embed = discord.Embed(title="The 20 minutes passed, game files deleted.", color = discord.Colour.red())
            await ctx.author.send(embed=embed)
        except Exception as e:
            if "Cannot send messages to this user" in str(e):
                embed = discord.Embed(title=getlang(f"{lang}_global_pm_disabled"), color = discord.Colour.red())
                await ctx.send(embed=embed)
            else:
                print(e)

@client.command()
async def deluser(ctx, arg1=None):
    language = checklang(ctx.guild.id)
    if language is False:
        await ctx.send("An error occured with the language selector.")
        return
    lang = language[0]
    server_config = language[1]
    try:
        arg1 = await commands.MemberConverter().convert(ctx, arg1)
    except:
        embed = discord.Embed(description=getlang(f"{lang}_global_cant_find_user_error"), color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    print("command used: ps!deluser")
    userid = str(arg1.id)
    authorid = str(ctx.author.id)
    puser = is_admin(authorid, server_config)
    if puser is not True:
        embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    check_has_gdps = has_gdps(userid)
    if check_has_gdps == True:
        cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [ctx.author.id])
        data = cursor.fetchall()
        if server_config != data[0][8]:
            await ctx.send("This GDPS wasn't created on this discord server, you can't delete it.")
            return
        cursor = execute_sql("delete from gdps_creator_userdata where userID = %s", [userid])
        embed = discord.Embed(title=getlang(f"{lang}_cdeluser_confirmation_title"), description=f"**{arg1.name}** " + getlang(f"{lang}_cdeluser_confirmation_description"), color = discord.Colour.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description=f"**{arg1.name}** " + getlang(f"{lang}_cdeluser_not_in_database_error"), color = discord.Colour.red())
        await ctx.send(embed=embed)

@client.command()
async def getdownload(ctx):
    right_channel = await in_right_channel(ctx)
    userid = None
    if not right_channel:
        return
    print("command used: ps!getdownload")
    userid = str(ctx.author.id)
    cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [userid])
    user = cursor.fetchall()
    check_has_gdps = has_gdps(userid)
    if check_has_gdps == True:
        cooldown_check = await command_cooldown(ctx, userid, "getdownload", 3600000)
        if cooldown_check:
            return
        else:
            if user[0][5] == 0:
                try:
                    user_custom_url = user[0][2]
                    user_gdps_name = user[0][1]
                    user_gdps_version = user[0][3]
                    pc_download_link = f"https://ps.fhgdps.com/tools/download/{user_custom_url}/{user_gdps_name}.zip"
                    mobile_download_link = f"https://ps.fhgdps.com/tools/download/{user_custom_url}/{user_gdps_name}.apk"

                    embed = discord.Embed(description="When the links are ready you will recieve a private message with the link to download it", color = discord.Colour.green())
                    await ctx.send(embed=embed)
                    process = await asyncio.create_subprocess_shell(f'./CreateDownload-Bot.sh {user_gdps_name} {user_gdps_version} {user_custom_url}')
                    await process.communicate()
                    embed = discord.Embed(title="Your download liks are ready!", description=f"You have 10 minutes to download your GDPS here:\n\n [PC Version]({pc_download_link})\n[Mobile Version]({mobile_download_link})", color = discord.Colour.green())
                    await ctx.author.send(embed=embed)

                    await asyncio.sleep(600)
                    shutil.rmtree(f"/var/www/gdps/tools/download/{user_custom_url}")
                    embed = discord.Embed(title="Download link deleted.", color = discord.Colour.red())
                    await ctx.author.send(embed=embed)
                except Exception as e:
                    if "Cannot send messages to this user" in str(e):
                        embed = discord.Embed(title="You have private messages disabled, enable them and try again.", color = discord.Colour.red())
                        await ctx.send(embed=embed)
                    else:
                        print(e)
            else:
                embed = discord.Embed(title="Your gdps got deleted because you left the server.", color = discord.Colour.red())
                await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="You don't have a GDPS!", color = discord.Colour.red())
        await ctx.send(embed=embed)

@client.command()
async def delgdps(ctx, arg1=None):
    language = checklang(ctx.guild.id)
    if language is False:
        await ctx.send("An error occured with the language selector.")
        return
    lang = language[0]
    server_config = language[1]
    try:
        arg1 = await commands.MemberConverter().convert(ctx, arg1)
    except:
        embed = discord.Embed(description=getlang(f"{lang}_cdeluser_cant_find_user_error"), color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    userid = str(arg1.id)
    puser = is_admin(ctx.author.id, server_config)
    if puser is not True:
        embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    check_has_gdps = has_gdps(userid)
    if check_has_gdps == True:
        cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [arg1.id])
        data = cursor.fetchall()
        if server_config != data[0][8]:
            await ctx.send("This GDPS wasn't created on this discord server, you can't delete it.")
            return
        process = await asyncio.create_subprocess_shell(f'./DelGDPS-Bot.sh {data[0][2]}')
        await process.communicate()
        cursor = execute_sql("delete from gdps_creator_userdata where userID = %s", [userid])
        embed = discord.Embed(title=getlang(f"{lang}_cdelgdps_deletion_title"), description=f"<@{arg1.id}>" + getlang(f"{lang}_cdelgdps_deletion_description"), color = discord.Colour.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description=getlang(f"{lang}_global_plural_no_gdps_error"), color = discord.Colour.red())
        await ctx.send(embed=embed)

@client.command()
async def permission(ctx, arg1="null", arg2="null"):
    print("command used: ps!permission")
    language = checklang(ctx.guild.id)
    if language is False:
        await ctx.send("An error occured with the language selector.")
        return
    lang = language[0]
    server_config = language[1]
    if ctx.author.id != 195598321501470720:
        embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
        await ctx.send(embed=embed)
    try:
        arg2 = await commands.MemberConverter().convert(ctx, arg2)
        userid = str(arg2.id)
    except:
        embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    cursor = execute_sql("select authorised_users from gdps_creator_config where id = %s", [server_config])
    data = cursor.fetchall()
    if data[0][0] == "[]":
        mod_list = []
    else:
        replaced = data[0][0].strip("][").replace(",", "")
        mod_list = replaced.split()
    if arg1 == "give":
        if userid in str(data):
            embed = discord.Embed(description="This user already has permissions to use admin commands.", color = discord.Colour.red())
            await ctx.send(embed=embed)
        else:
            mod_list.append(arg2.id)
            mod_list = map(int, mod_list)
            mod_list = list(mod_list)
            cursor = execute_sql("update gdps_creator_config set authorised_users = %s where id = %s", [str(mod_list), server_config])
            embed = discord.Embed(description=f"<@{arg2.id}> can now use admin commands!", color = discord.Colour.green())
            await ctx.send(embed=embed)
    elif arg1 == "remove":
        if userid in str(data):
            mod_list.remove(str(arg2.id))
            mod_list = map(int, mod_list)
            mod_list = list(mod_list)
            cursor = execute_sql("update gdps_creator_config set authorised_users = %s where id = %s", [str(mod_list), server_config])
            embed = discord.Embed(description=f"<@{arg2.id}> no longer has permission to use admin commands!", color = discord.Colour.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="This user didn't have permission to use admin commands.", color = discord.Colour.red())
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description="Invalid option.", color = discord.Colour.red())
        await ctx.send(embed=embed)

@client.command()
async def info(ctx, arg1=None):
    right_channel = await in_right_channel(ctx)
    if not right_channel:
        return
    language = checklang(ctx.guild.id)
    if language is False:
        await ctx.send("An error occured with the language selector.")
        return
    lang = language[0]
    if arg1 is None:
        userid = str(ctx.author.id)
        no_gdps_msg = "You don't have a GDPS!"
        embed_title = "Your GDPS info"
        gdps_deleted = "Your gdps got deleted because you left the server."
    else:
        try:
            arg1 = await commands.MemberConverter().convert(ctx, arg1)
        except:
            embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        userid = str(arg1.id)
        no_gdps_msg = "This user doesn't have a GDPS!"
        embed_title = "Info of " + arg1.name + "'s GDPS"
        gdps_deleted = "The GDPS of this user got deleted because he left the server."

    check_has_gdps = has_gdps(userid)
    if check_has_gdps == True:
        cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [userid])
        data = cursor.fetchall()
        if data[0][5] == 1:
            embed = discord.Embed(title=gdps_deleted, color = discord.Colour.red())
            await ctx.send(embed=embed)
        else:
            if data[0][8] == "gdpsfh":
                created_in = "GDPS Free Hosting"
            elif data[0][8] == "gdpsfhru":
                created_in = "GDPS Free Hosting RU"
            elif data[0][8] == "gdpshub":
                created_in = "GDPS Hub"
            else:
                created_in = "Unknown"

            api_banned = "Unknown"
            if data[0][10] == 1:
                api_banned = "No"
            elif data[0][10] == 0:
                api_banned = "Yes"

            embed = discord.Embed(title=embed_title, description = f"**Server name** : {data[0][1]} \n**Custom URL** : {data[0][2]} \n**Original version** : {data[0][3]} \n**Created in** : {created_in} \n**API Banned** : {api_banned}", color = discord.Colour.green())
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title=no_gdps_msg, color = discord.Colour.red())
        await ctx.send(embed=embed)

@client.command()
async def offinfo(ctx, arg1=None):
    user = await client.fetch_user(arg1)
    if arg1 is None:
        embed = discord.Embed(description="You need to specify a user!", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    else:
        userid = str(user.id)
        no_gdps_msg = "This user doesn't have a GDPS!"
        embed_title = "Info of " + user.name + "'s GDPS"
        gdps_deleted = "The GDPS of this user got deleted because he left the server."

    check_has_gdps = has_gdps(userid)
    if check_has_gdps == True:
        cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [user.id])
        data = cursor.fetchall()
        if data[0][5] == 1:
            embed = discord.Embed(title=gdps_deleted, color = discord.Colour.red())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title=embed_title, description = f"**Server name** : {data[0][1]} \n**Custom URL** : {data[0][2]} \n**Original version** : {data[0][3]}", color = discord.Colour.green())
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title=no_gdps_msg, color = discord.Colour.red())
        await ctx.send(embed=embed)

@client.command()
async def delete(ctx):
    right_channel = await in_right_channel(ctx)
    if not right_channel:
        return
    language = checklang(ctx.guild.id)
    print("command used: ps!delete")
    userid = str(ctx.author.id)
    check_has_gdps = has_gdps(userid)
    if check_has_gdps == True:
        cooldown_check = await command_cooldown(ctx, userid, "delete", 10800000)
        if cooldown_check:
            return
        else:
            cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [ctx.author.id])
            data = cursor.fetchall()
            if data[0][5] == 0:
                embed = discord.Embed(title="Are you sure that you want to delete your gdps? all your data will be gone. (yes/no)", color = discord.Colour.from_rgb(255, 128, 0))
                await ctx.send(embed=embed)
                confirmation = await client.wait_for('message', check=lambda message: message.author == ctx.author)
                if confirmation.content.lower() == "yes":
                    process = await asyncio.create_subprocess_shell(f'./DelGDPS-Bot.sh {data[0][2]}')
                    await process.communicate()
                    cursor = execute_sql("delete from gdps_creator_userdata where userID = %s", [userid])
                    embed = discord.Embed(title="Your gdps got deleted!", color = discord.Colour.green())
                    await ctx.send(embed=embed)
                elif confirmation.content == "no":
                    with open("on_cooldown.json", "r+") as cooldown_file:
                        cooldown_data = json.load(cooldown_file)
                        cooldown_file.seek(0)
                        del cooldown_data[userid]["delete"]
                        json.dump(cooldown_data, cooldown_file, indent=4)
                        cooldown_file.truncate()
                        embed = discord.Embed(title="GDPS deletion cancelled!", color = discord.Colour.green())
                        await ctx.send(embed=embed)
                else:
                    with open("on_cooldown.json", "r+") as cooldown_file:
                        cooldown_data = json.load(cooldown_file)
                        cooldown_file.seek(0)
                        del cooldown_data[userid]["delete"]
                        json.dump(cooldown_data, cooldown_file, indent=4)
                        cooldown_file.truncate()
                    await ctx.send("Not a valid answer")
            else:
                embed = discord.Embed(title="Your gdps got deleted because you left the server.", color = discord.Colour.red())
                await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="You don't have a GDPS!", color = discord.Colour.red())
        await ctx.send(embed=embed)

@client.command()
async def gdpsbrowser(ctx, arg1 = None):
    right_channel = await in_right_channel(ctx)
    if not right_channel:
        return
    is_donator = await check_donator(ctx)
    if is_donator is False:
        return
    if ctx.author.id in in_setup_gdpsbrowser:
        await ctx.send("Finish your current setup first!")
        return
    print("command used: ps!gdpsbrowser")
    userid = str(ctx.message.author.id)
    cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [ctx.author.id])
    data = cursor.fetchall()
    check_has_gdps = has_gdps(userid)
    if check_has_gdps == True:
        if data[0][5] == 0:
            if data[0][7] == 1:
                await ctx.send("You are already on gdpsbrowser.com!")
                return
            gdps_curl = data[0][2]
            in_setup_gdpsbrowser.append(ctx.author.id)

            embed = discord.Embed(description="Type your GDPS name that will displayed on the website", color = discord.Colour.from_rgb(255, 128, 0))
            await ctx.send(embed=embed)
            gdps_name = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            gdps_name = gdps_name.content
            
            embed = discord.Embed(description="Type the GDPS owner name that will be displayed on the website", color = discord.Colour.from_rgb(255, 128, 0))
            await ctx.send(embed=embed)
            gdps_author_name = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            gdps_author_name = gdps_author_name.content

            embed = discord.Embed(description="Link that users will be redirected to, can be any link like a discord server / youtube channel/ twitch link, whatever you want.", color = discord.Colour.from_rgb(255, 128, 0))
            await ctx.send(embed=embed)
            gdps_author_pub = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            gdps_author_pub = gdps_author_pub.content

            url = "https://api.cloudflare.com/client/v4/zones/f432e22c3a07264921c8a1f22acaecef/dns_records"
            headers = {"X-Auth-Email": cloudflare_email,
                        "X-Auth-Key": cloudflare_api_key,
                        "Content-type": "application/json"}
            req_data = {"type": "CNAME",
                        "name": f"{gdps_curl}.gdpsbrowser.com",
                        "content": "gdpsbrowser.com",
                        "ttl": 1,
                        "proxied": True}
            
            try:
                req = requests.post(url, data=json.dumps(req_data), headers=headers, timeout=5)
            except Exception as e:
                print(e)
                await ctx.send("An error occured with the cloudflare api.")
                return

            with open("/home/gdps/gdps_browser/servers.json", "r+") as servers_file:
                servers_data = json.load(servers_file)
                servers_file.seek(0)
                json_data = {"name": gdps_name,
                                "link": f"http://ps.fhgdps.com/{gdps_curl}/",
                                "author": gdps_author_name,
                                "authorLink": gdps_author_pub,
                                "id": gdps_curl,
                                "endpoint": f"http://ps.fhgdps.com/{gdps_curl}/"}
                servers_data.insert(len(servers_data), json_data)
                json.dump(servers_data, servers_file, indent=4)

            process = await asyncio.create_subprocess_shell(f'screen -X -S GDPS-Browser quit')
            await process.communicate()
            process = await asyncio.create_subprocess_shell(f'cd /home/gdps/gdps_browser/ && screen -d -m S GDPS-Bro-wser node index.js')
            await process.communicate()
            
            cursor = execute_sql("update gdps_creator_userdata set on_gdps_browser = 1 where userID = %s", [userid])
            embed = discord.Embed(description="Your gdps was added to https://gdpsbrowser.com/ !", color = discord.Colour.green())
            await ctx.send(embed=embed)
            in_setup_gdpsbrowser.remove(ctx.author.id)
    else:
        embed = discord.Embed(title="You don't have a GDPS!", color = discord.Colour.red())
        await ctx.send(embed=embed)

@client.command()
async def destroy(ctx):
    await ctx.send("https://tenor.com/view/nuke-press-the-button-bomb-them-nuke-them-cat-gif-16361990")

@client.command()
async def power(ctx, option = None, status = None):
    if ctx.author.id != 195598321501470720:
        await ctx.send("no")
        return
    if option is None:
        await ctx.send("Please enter an option: apache, mysql, ftp")
        return
    if status is None:
        await ctx.send("Please enter a service status: on, off")
        return
    if option == "apache":
        if status == "on":
            process = await asyncio.create_subprocess_shell(f'service apache2 start')
            await process.communicate()
        elif status == "off":
            process = await asyncio.create_subprocess_shell(f'service apache2 stop')
            await process.communicate()
    elif option == "mysql":
        if status == "on":
            process = await asyncio.create_subprocess_shell(f'service mysql start')
            await process.communicate()
        elif status == "off":
            process = await asyncio.create_subprocess_shell(f'service mysql stop')
            await process.communicate()
    elif option == "ftp":
        if status == "on":
            process = await asyncio.create_subprocess_shell(f'service proftpd start')
            await process.communicate()
        elif status == "off":
            process = await asyncio.create_subprocess_shell(f'service proftpd stop')
            await process.communicate()
    await ctx.send("Done!")

@client.command()
async def help(ctx, arg1="null"): 
    if arg1 == "admin":
        embed = discord.Embed(title="GDPS Creator admin commands", description = f"**{prefix}deluser** : Delete a user from the DB\n"
                                                                               + f"**{prefix}delgdps <user>** : Delete a gdps\n"
                                                                               + f"**{prefix}rc <cooldown> <user>** : Removes the cooldown of a specific command\n"
                                                                               + f"**{prefix}lockdown <enable/disable>** : Enable / Disable the option to create new gdps\n"
                                                                               + f"**{prefix}banwave** : Ban users that left the server and delete their GDPS\n"
                                                                               + f"**{prefix}delallgdps** : NANI??\n", color = discord.Colour.red())
    else:
        embed = discord.Embed(title="GDPS Creator commands", description = f"**{prefix}c** : Start your GDPS setup\n"
                                                                         + f"**{prefix}info** : Displays the info of your GDPS\n"
                                                                         + f"**{prefix}logininfo** : Gives you the login info for phpmyadmin with no embeds\n"
                                                                         + f"**{prefix}getbackup** : Create a downloadable backup of your GDPS\n"
                                                                         + f"**{prefix}changepass** : Change the password of your gdps\n"
                                                                         + f"**{prefix}delete** : Delete your gdps\n"
                                                                         + f"**{prefix}status** : Shows the current server status\n"
                                                                         + f"**{prefix}lockdown** : Shows if lockdown is activated\n"
                                                                         + f"**{prefix}access** <add/remove> <user>: Gives the user access to use admin commands on your GDPS\n"
                                                                         + f"**{prefix}credits** : Shows some infos about the bot", color = discord.Colour.red())
    await ctx.send(embed=embed)

@client.command()
async def fixftp(ctx):
    if ctx.author.id != 195598321501470720:
        await ctx.send("no")
        return
    cursor = execute_sql("select gdps_custom_url,gdps_password from gdps_creator_userdata where left_server = 0")
    gdps_curl = cursor.fetchall()
    for gcurl in gdps_curl:
        curl = gcurl[0]
        password = gcurl[1]
        process = await asyncio.create_subprocess_shell(f'./CreateFTP-Bot.sh {curl} {password}')
        await process.communicate()
        print(f"create ftp: {curl}")
    await ctx.send("done.")

@client.command()
async def delftp(ctx):
    if ctx.author.id != 195598321501470720:
        await ctx.send("no")
        return
    cursor = execute_sql("select gdps_custom_url from gdps_creator_userdata")
    gdps_curl = cursor.fetchall()
    for gcurl in gdps_curl:
        curl = gcurl[0]
        process = await asyncio.create_subprocess_shell(f'deluser gdps_{curl}')
        await process.communicate()
        print(f"delete ftp: {curl}")
    await ctx.send("done.")

@client.command()
async def fixdata(ctx):
    if ctx.author.id != 195598321501470720:
        await ctx.send("no")
        return
    cursor = execute_sql("select * from gdps_creator_userdata")
    data = cursor.fetchall()
    folders = os.listdir("/var/www/gdps")
    count = 0
    total_gdps = 0
    wait_ban = []
    curl_in_db = []
    for curl in data:
        total_gdps += 1
        if curl[5] != 1:
            curl_in_db.append(curl[2])
    for directories in folders:
        if str(directories) not in str(curl_in_db):
            count += 1
            wait_ban.append(directories)
    await ctx.send(f"{len(wait_ban)} curl are in the ban list")
    confirmation = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    confirmation = confirmation.content.lower()
    if confirmation != "yes":
        await ctx.send("Cancelled.")
        return
    await ctx.send(f"{count} are not in the db, starting deletion process")
    for curl in wait_ban:
        process = await asyncio.create_subprocess_shell(f'./DelGDPS-Bot.sh {curl}')
        await process.communicate()
    await ctx.send("done.")

@client.command()
async def fixapk(ctx):
    right_channel = await in_right_channel(ctx)
    if not right_channel:
        return
    userid = ctx.author.id
    check_has_gdps = has_gdps(userid)
    if check_has_gdps == True:
        cooldown_check = await command_cooldown(ctx, userid, "fixapk", 86400000)
        if cooldown_check:
            return
        embed = discord.Embed(title="<a:loading:762295133747413022> Trying to fix your GDPS APK please wait..", color = discord.Colour.green())
        message = await ctx.send(embed=embed)
        cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [userid])
        data = cursor.fetchall()
        process = await asyncio.create_subprocess_shell(f'./FixAPK-Bot.sh {data[0][1]} {str(data[0][2])}')
        await process.communicate()
        await message.delete()
        embed = discord.Embed(title="APK successfully fixed!", color = discord.Colour.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="You don't have a GDPS!", color = discord.Colour.red())
        await ctx.send(embed=embed)

@client.command()
async def getbackup(ctx, arg1=None, offline=None):
    right_channel = await in_right_channel(ctx)
    userid = None
    language = checklang(ctx.guild.id)
    if language is False:
        await ctx.send("An error occured with the language selector.")
        return
    lang = language[0]
    if not right_channel:
        return
    arg1_data = None
    if arg1 is not None:
        try:
            arg1 = await commands.MemberConverter().convert(ctx, arg1)
        except:
            if offline is None:
                embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
                await ctx.send(embed=embed)
                return
            else:
                arg1 = await client.fetch_user(arg1)
        #if ctx.author.id != 195598321501470720 and ctx.author.id != 180790976128745472:
            #is_donator = await check_donator(ctx, arg1)
            #if is_donator is False:
                #return
        cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [arg1.id])
        arg1_data = cursor.fetchall()
    #else:
        #is_donator = await check_donator(ctx)
        #if is_donator is False:
            #return
    print("command used: ps!getbackup")
    userid = str(ctx.author.id)
    cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [userid])
    user = cursor.fetchall()
    if arg1 is not None:
        if userid not in arg1_data[0][6] and ctx.author.id != 195598321501470720:
            embed = discord.Embed(description=f"You don't have access to this GDPS!", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        else:
            user = arg1_data
    check_has_gdps = has_gdps(userid)
    if check_has_gdps == True:
        cooldown_check = await command_cooldown(ctx, userid, "getbackup", 3600000)
        if cooldown_check:
            return
        else:
            if user[0][5] == 0:
                try:
                    printable = f'{string.ascii_letters}{string.digits}'
                    printable = list(printable)
                    random.shuffle(printable)
                    random_id = random.choices(printable, k=30)
                    backup_id = ''.join(random_id)
                    user_custom_url = user[0][2]
                    download_link = f"https://backups.fhgdps.com/backup/{backup_id}/{user_custom_url}-backup.zip"

                    embed = discord.Embed(description="When the backup will be created you will recieve a private message with the link to download it", color = discord.Colour.green())
                    await ctx.send(embed=embed)
                    process = await asyncio.create_subprocess_shell(f'./CreateBackup-Bot.sh {user[0][2]} {backup_id}')
                    await process.communicate()
                    if arg1 is None:
                        embed = discord.Embed(title="Your backup is ready!", description=f"You have 10 minutes to download your backup here: [Link]({download_link})", color = discord.Colour.green())
                        await ctx.author.send(embed=embed)
                    else:
                        embed = discord.Embed(title=f"The backup from {arg1.name}'s GDPS is ready!", description=f"You have 10 minutes to download the backup here: [Link]({download_link})", color = discord.Colour.green())
                        await ctx.author.send(embed=embed)
                        embed = discord.Embed(description=f"{ctx.author.name} ({ctx.author.id}) created a backup of your gdps.", color = discord.Colour.green())
                        await arg1.send(embed=embed)

                    await asyncio.sleep(600)
                    shutil.rmtree("/var/www/gdps/tools/backup/" + backup_id)
                    embed = discord.Embed(title="Backup deleted.", color = discord.Colour.red())
                    await ctx.author.send(embed=embed)
                except Exception as e:
                    if "Cannot send messages to this user" in str(e):
                        if userid == str(ctx.author.id):
                            embed = discord.Embed(title="You have private messages disabled, enable them and try again.", color = discord.Colour.red())
                            await ctx.send(embed=embed)
                        else:
                            embed = discord.Embed(title="You or the GDPS owner have private messages disabled, enable them and try again.", color = discord.Colour.red())
                            await ctx.send(embed=embed)
                    else:
                        print(e)
            else:
                embed = discord.Embed(title="Your gdps got deleted because you left the server.", color = discord.Colour.red())
                await ctx.send(embed=embed)
    else:
        if userid == str(ctx.author.id):
            embed = discord.Embed(title="You don't have a GDPS!", color = discord.Colour.red())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="This user doesn't have a GDPS!", color = discord.Colour.red())
            await ctx.send(embed=embed)

@client.command()
async def changepass(ctx, arg1=None):
    right_channel = await in_right_channel(ctx)
    if not right_channel:
        return
    language = checklang(ctx.guild.id)
    if language is False:
        await ctx.send("An error occured with the language selector.")
        return
    lang = language[0]
    if arg1 is not None:
        try:
            arg1 = await commands.MemberConverter().convert(ctx, arg1)
        except:
            embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
    print("command used: ps!changepass")
    userid = str(ctx.message.author.id)
    cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [userid])
    user = cursor.fetchall()
    if arg1 != None:
        cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [arg1.id])
        arg1_data = cursor.fetchall()
        if int(userid) not in arg1_data[0][6]:
            embed = discord.Embed(description=f"You don't have access to this GDPS!", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        else:
            user = arg1_data
    check_has_gdps = has_gdps(userid)
    if check_has_gdps == True:
        cooldown_check = await command_cooldown(ctx, userid, "changepass", 1800000)
        if cooldown_check:
            return
        else:
            if user[0][5] == 0:
                try:
                    printable = f'{string.ascii_letters}{string.digits}'
                    printable = list(printable)
                    random.shuffle(printable)
                    random_password = random.choices(printable, k=22)
                    password = ''.join(random_password)

                    process = await asyncio.create_subprocess_shell(f'./ChangePass-Bot.sh {user[0][2]} {password}')
                    await process.communicate()
                    cursor = execute_sql("update gdps_creator_userdata set gdps_password = %s where userID = %s", [password, userid])
                    
                    if arg1 is None:
                        embed = discord.Embed(description="Your new password was sent to you in your private messages!", color = discord.Colour.green())
                        await ctx.send(embed=embed)
                        embed = discord.Embed(title="Password changed!", description=f"New password: {password}", color = discord.Colour.green())
                        await ctx.message.author.send(embed=embed)
                    else:
                        embed = discord.Embed(description="The new password was sent to you and the gdps owner in private messages!", color = discord.Colour.green())
                        await ctx.send(embed=embed)
                        embed = discord.Embed(title=f"The password from {arg1.name}'s GDPS has been changed!", description=f"New password: {password}", color = discord.Colour.green())
                        await ctx.message.author.send(embed=embed)
                        embed = discord.Embed(title=f"Password changed by {ctx.author.name} ({ctx.author.id})!", description=f"New password: {password}", color = discord.Colour.green())
                        await arg1.send(embed=embed)
                except Exception as e:
                    if "Cannot send messages to this user" in str(e):
                        if userid == str(ctx.author.id):
                            embed = discord.Embed(title="You have private messages disabled, enable them and try again. (The password has been changed anyway)", color = discord.Colour.red())
                            await ctx.send(embed=embed)
                        else:
                            embed = discord.Embed(title="You or the GDPS owner have private messages disabled, enable them and try again. (The password has been changed anyway)", color = discord.Colour.red())
                            await ctx.send(embed=embed)
                    else:
                        print(e)
            else:
                embed = discord.Embed(title="Your gdps got deleted because you left the server.", color = discord.Colour.red())
                await ctx.send(embed=embed)
    else:
        if userid == str(ctx.author.id):
            embed = discord.Embed(title="You don't have a GDPS!", color = discord.Colour.red())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="This user doesn't have a GDPS!", color = discord.Colour.red())
            await ctx.send(embed=embed)

@client.command()
async def logininfo(ctx, arg1=None):
    right_channel = await in_right_channel(ctx)
    if not right_channel:
        return
    language = checklang(ctx.guild.id)
    if language is False:
        await ctx.send("An error occured with the language selector.")
        return
    lang = language[0]
    userid = str(ctx.message.author.id)
    cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [userid])
    user = cursor.fetchall()
    if arg1 != None:
        try:
            arg1 = await commands.MemberConverter().convert(ctx, arg1)
        except:
            embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        cursor = execute_sql("select * from gdps_creator_userdata where userID = %s", [arg1.id])
        arg1_data = cursor.fetchall()
        if str(userid) not in arg1_data[0][6] and ctx.author.id != 195598321501470720:
            embed = discord.Embed(description=f"You don't have access to this GDPS!", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        else:
            user = arg1_data
    check_has_gdps = has_gdps(userid)
    if check_has_gdps == True:
        if user[0][5] == 0:
            try:
                if arg1 is None:
                    await ctx.author.send(f"Your phpmyadmin login info:\n\nUser: gdps_{user[0][2]}\nPassword: {user[0][4]}")
                    embed = discord.Embed(title="Your phpmyadmin login info was sent to you in private messages!", color = discord.Colour.green())
                    await ctx.send(embed=embed)
                else:
                    await ctx.author.send(f"{arg1.name}'s GDPS phpmyadmin login info:\n\nUser: gdps_{user[0][2]}\nPassword: {user[0][4]}")
                    embed = discord.Embed(description=f"{arg1.name}'s GDPS login info was sent to you in private messages!", color = discord.Colour.green())
                    await ctx.send(embed=embed)
                    embed = discord.Embed(description=f"{ctx.author.name} ({ctx.author.id}) entered the gdps!logininfo command on your gdps to get your GDPS database infos.", color = discord.Colour.green())
                    await arg1.send(embed=embed)
            except Exception as e:
                if "Cannot send messages to this user" in str(e):
                    if userid == str(ctx.author.id):
                        embed = discord.Embed(title="You have private messages disabled, enable them and try again.", color = discord.Colour.red())
                        await ctx.send(embed=embed)
                    else:
                        embed = discord.Embed(title="You or the GDPS owner have private messages disabled, enable them and try again.", color = discord.Colour.red())
                        await ctx.send(embed=embed)
                else:
                    print(e)
        else:
            embed = discord.Embed(title="Your gdps got deleted because you left the server.", color = discord.Colour.red())
            await ctx.send(embed=embed)
    else:
        if userid == str(ctx.author.id):
            embed = discord.Embed(title="You don't have a GDPS!", color = discord.Colour.red())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="This user doesn't have a GDPS!", color = discord.Colour.red())
            await ctx.send(embed=embed)

@client.command()
async def access(ctx, arg1="null", user=None):
    right_channel = await in_right_channel(ctx)
    if not right_channel:
        return
    language = checklang(ctx.guild.id)
    if language is False:
        await ctx.send("An error occured with the language selector.")
        return
    lang = language[0]
    is_donator = await check_donator(ctx)
    if is_donator is False:
        return
    print("command used: ps!mod")
    authorid = str(ctx.author.id)
    check_has_gdps = has_gdps(authorid)
    if check_has_gdps == False:
        embed = discord.Embed(description="You don't have a gdps!", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    else:
        try:
            user = await commands.MemberConverter().convert(ctx, user)
        except:
            embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        cursor = execute_sql("select moderators from gdps_creator_userdata where userID = %s", [ctx.author.id])
        data = cursor.fetchall()
        if data[0][0] == "[]":
            mod_list = []
        else:
            replaced = data[0][0].strip("][").replace(",", "")
            mod_list = replaced.split()
        if arg1 == "add":
            if user.id == ctx.author.id:
                embed = discord.Embed(description=f"Why are you trying to give yourself permissions? Won't question it but you can't do that since you already have permissions..", color = discord.Colour.red())
                await ctx.send(embed=embed)
                return
            if str(user.id) in mod_list:
                embed = discord.Embed(description=f"**{user.name}** can already access your GDPS!", color = discord.Colour.red())
                await ctx.send(embed=embed)
                return
            else:
                mod_list.append(user.id)
                mod_list = map(int, mod_list)
                mod_list = list(mod_list)
                cursor = execute_sql("update gdps_creator_userdata set moderators = %s where userID = %s", [str(mod_list), ctx.author.id])
                
                embed = discord.Embed(description=f"**{user.name}** now has access to your GDPS!", color = discord.Colour.green())
                await ctx.send(embed=embed)
        elif arg1 == "remove":
            if str(user.id) in mod_list:
                mod_list.remove(str(user.id))
                mod_list = map(int, mod_list)
                mod_list = list(mod_list)
                cursor = execute_sql("update gdps_creator_userdata set moderators = %s where userID = %s", [str(mod_list), ctx.author.id])
                
                embed = discord.Embed(description=f"**{user.name}** can no longer access your GDPS!", color = discord.Colour.green())
                await ctx.send(embed=embed)
                return
            else:
                embed = discord.Embed(description=f"**{user.name}** never had access to your GDPS!", color = discord.Colour.red())
                await ctx.send(embed=embed)
                return
        elif arg1 == "list":
            mods_counter = 0
            mods_list = []
            for mods in mod_list:
                mods_counter += 1
                mod = client.get_user(int(mods))
                mods_list.append(mod.mention + "\n")
            embed = discord.Embed(title="Your GDPS access list", description="".join(map(str, mods_list)), color = discord.Colour.green())
            if mods_counter == 0:
                embed = discord.Embed(description="No one has access to your gdps!", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        else:
            embed = discord.Embed(description=f"This option is not valid!", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return

@client.command()
async def sendallmsg(ctx, *, message):
    if ctx.author.id != 195598321501470720:
        await ctx.send("no")
        return
    await ctx.send("Do you really want to send this?")
    confirmation = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    if confirmation.content != "yes":
        await ctx.send("cancelled.")
        return
    cursor = execute_sql("select userID from gdps_creator_userdata")
    #users_ids = cursor.fetchall()
    users_ids = [195598321501470720, 657974350867070977]
    await ctx.send("ok sending")
    for user_id in users_ids:
        if user_id == 176967674176208896 or user_id == 373128858687373323 or user_id == 307626404181311488:
            continue
        else:
            try:
                user = client.get_user(user_id)
                if str(743032231995506778) in str(user.roles):
                    await user.send(message)
                    print(f"Sent a message to {user.name}")
            except Exception as e:
                print(e)
                print(f"Couldn't send a message to {user.name}")
    await ctx.send("Done")

@client.command()
async def delallgdps(ctx):
    """
    if ctx.message.author.id != 195598321501470720:
        await ctx.send("no")
        return
    cursor = execute_sql("select delallgdps_command from gdps_creator_config where id = 'gdpsfh'")
    command_enabled = cursor.fetchall()
    if command_enabled[0][0] != 1:
        embed = discord.Embed(description="This command is disabled for security reasons, the only way to use it is to enable it in the config.", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    """
    embed = discord.Embed(description="Are you sure that you want to delete all gdps?", color = discord.Colour.green())
    await ctx.send(embed=embed)
    warn1 = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    if warn1.content.lower() == "yes":
        embed = discord.Embed(description="Are you really sure???", color = discord.Colour.orange())
        await ctx.send(embed=embed)
        warn2 = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        if warn2.content.lower() == "yes":
            embed = discord.Embed(description="100% SURE??????", color = discord.Colour.red())
            await ctx.send(embed=embed)
            warn3 = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            if warn3.content.lower() == "yes":
                embed = discord.Embed(title=f"<a:loading:762295133747413022> Deleting 8575 GDPS please wait...", color = discord.Colour.green())
                delete_msg = await ctx.send(embed=embed)
                await asyncio.sleep(30)
                await delete_msg.delete()
                embed = discord.Embed(title=f"Deleted 3982 GDPS!", color = discord.Colour.green())
                await ctx.send(embed=embed)
                await asyncio.sleep(15)
                await ctx.send("https://tenor.com/view/dance-moves-dancing-singer-groovy-gif-17029825")
                """
                await ctx.send("https://tenor.com/view/nuke-press-the-button-bomb-them-nuke-them-cat-gif-16361990")
                gdps_count = 0
                cursor = execute_sql("select * from gdps_creator_userdata")
                data = cursor.fetchall()
                for curl in data:
                    if curl[5] != 1:
                        gdps_count += 1
                        process = await asyncio.create_subprocess_shell(f'./DelGDPS-Bot.sh {curl[2]}')
                        await process.communicate()
                process = await asyncio.create_subprocess_shell(f'service apache2 reload')
                await process.communicate()
                embed = discord.Embed(title=f"Deleted {gdps_count} GDPS!", color = discord.Colour.green())
                await ctx.send(embed=embed)
                """
            else:
                embed = discord.Embed(title="You just stopped a disaster..", color = discord.Colour.green())
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="You just stopped a disaster..", color = discord.Colour.green())
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="You just stopped a disaster..", color = discord.Colour.green())
        await ctx.send(embed=embed)

@client.command()
async def lockdown(ctx, arg1="null"):
    language = checklang(ctx.guild.id)
    if language is False:
        await ctx.send("An error occured with the language selector.")
        return
    lang = language[0]
    server_config = language[1]
    userid = str(ctx.message.author.id)
    current_time = time.time_ns() // 1_000_000
    cursor = execute_sql("select * from gdps_creator_config where id = %s", [server_config])
    data = cursor.fetchall()
    if arg1 == "null":
        if data[0][1] == 1:
            lockdown_start_time = int(data[0][2])
            time_substract = current_time-lockdown_start_time
            false_day = int(datetime.fromtimestamp(time_substract/1000).strftime("%d"))
            days = false_day-1
            false_hour = int(datetime.fromtimestamp(time_substract/1000).strftime("%H"))
            hours = false_hour-1
            minutes = int(datetime.fromtimestamp(time_substract/1000).strftime("%M"))
            seconds = int(datetime.fromtimestamp(time_substract/1000).strftime("%S"))
            time_format = f"{days} Days, {hours} Hours, {minutes} Minutes and {seconds} Seconds"
            if days >= 1:
                time_format = f"{days} Days, {hours} Hours, {minutes} Minutes and {seconds} Seconds"
            else:
                if hours >= 1:
                    time_format = f"{hours} Hours, {minutes} Minutes and {seconds} Seconds"
                else:
                    if minutes >= 1:
                        time_format = f"{minutes} Minutes and {seconds} Seconds"
                    else:
                        if days <= 0:
                            time_format = f"{hours} Hour, {minutes} Minutes and {seconds} Seconds"
                            if hours <= 1:
                                time_format = f"{minutes} Minute and {seconds} Seconds"
                                if minutes <= 0:
                                    time_format = f"{seconds} Seconds"

            embed = discord.Embed(title="Lockdown", description="**Status** : Enabled\n"
                                                                + f"**Activated since** : {time_format}", color = discord.Colour.green())
        elif data[0][1] == 0:
            embed = discord.Embed(title="Lockdown", description="**Status** : Disabled", color = discord.Colour.green())
        else:
            embed = discord.Embed(title="Lockdown", description="**Status** : Error", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    if userid in data[0][4]:
        if arg1 == "enable":
            if data[0][1] == 1:
                embed = discord.Embed(title="Lockdown is already enabled!", color = discord.Colour.red())
                await ctx.send(embed=embed)
            else:
                cursor = execute_sql("update gdps_creator_config set lockdown_status = 1 where id = %s", [server_config])
                cursor = execute_sql("update gdps_creator_config set lockdown_start_time = %s where id = %s", [current_time, server_config])
                embed = discord.Embed(title="Lockdown is now enabled!", color = discord.Colour.green())
                await ctx.send(embed=embed)
        elif arg1 == "disable":
            if data[0][1] == 0:
                embed = discord.Embed(title="Lockdown is already disabled!", color = discord.Colour.red())
                await ctx.send(embed=embed)
            else:
                cursor = execute_sql("update gdps_creator_config set lockdown_status = 0 where id = %s", [server_config])
                embed = discord.Embed(title="Lockdown is now disabled!", color = discord.Colour.green())
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="Invalid option.", color = discord.Colour.red())
            await ctx.send(embed=embed)
        
    else:
        embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
        await ctx.send(embed=embed)

@client.command()
async def rc(ctx, arg1="null", arg2=None):
    language = checklang(ctx.guild.id)
    if language is False:
        await ctx.send("An error occured with the language selector.")
        return
    lang = language[0]
    server_config = language[1]
    if arg1 == "null":
        await ctx.send("You need to type a cooldown type!")
        return
    if arg2 is None:
        await ctx.send("You need to ping someone or type their id!")
        return
    else:
        try:
            arg2 = await commands.MemberConverter().convert(ctx, arg2)
        except:
            embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
    userid = str(arg2.id)
    puser = is_admin(ctx.author.id, server_config)
    if puser is not True:
        embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    with open("on_cooldown.json", "r+") as file:
        data = json.load(file)
        file.seek(0)
        if userid in str(data):
            cooldown_exist = data[userid].get(arg1, "null")
            if cooldown_exist != "null":
                del data[userid][arg1]
                json.dump(data, file, indent=4)
                file.truncate()
                embed = discord.Embed(title=f"Cooldown reset", description=f"The **{arg1}** command cooldown was successfully reset for the user **{arg2.name}**!", color = discord.Colour.green())
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title=f"Cooldown reset", description=f"The **{arg1}** command is not on cooldown for the user **{arg2.name}** or doesn't exist.", color = discord.Colour.red())
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="This user doesn't have a gdps!", color = discord.Colour.red())
            await ctx.send(embed=embed)

@client.command()
async def status(ctx):
    right_channel = await in_right_channel(ctx)
    if not right_channel:
        return
    count_url = "http://api.fhgdps.com/infos/"
    count_data = {"key": web_api_key,
                  "data": "gdps_count"}
    ban_data = {"key": web_api_key,
                "data": "gdps_bans"}

    check_api_url = "http://api.fhgdps.com/status/"
    gdps_count = "API offline"
    gdps_bans = "API offline"
    api_status = "null"
    try:
        gdps_count = requests.get(count_url, params = count_data).json()
        gdps_bans = requests.get(count_url, params = ban_data).json()
        api_status = requests.get(check_api_url).json()
    except Exception as e:
        if "Failed to establish a new connection" in str(e):
            api_status = "no"
        else:
            print(e)

    mysql_request = os.system("systemctl is-active --quiet mariadb")
    ftp_request = os.system("systemctl is-active --quiet proftpd")
    apache_request = os.system("systemctl is-active --quiet apache2")
    mysql_emoji = "Error"
    ftp_emoji = "Error"
    apache_emoji = "Error"
    api_emoji = "Error"

    if api_status == 1:
        api_emoji = ":green_circle:"
    else:
        api_emoji = ":red_circle:"

    if mysql_request == 0:
        mysql_emoji = ":green_circle:"
    else:
        mysql_emoji = ":red_circle:"

    if ftp_request == 0:
        ftp_emoji = ":green_circle:"
    else:
        ftp_emoji = ":red_circle:"

    if apache_request == 0:
        apache_emoji = ":green_circle:"
    else:
        apache_emoji = ":red_circle:"

    if apache_emoji == ":green_circle:" and mysql_emoji == ":green_circle:":
        conclusion = "All gdps are online!"
    elif apache_emoji == ":red_circle:" and mysql_emoji == ":red_circle:":
        conclusion = "All main services are offline, all GDPS servers are down."
    elif apache_emoji == ":red_circle:" or mysql_emoji == ":red_circle:":
        conclusion = "One of the main service is offline, all GDPS servers are down."

    data_embed = discord.Embed(title="GDPS FH server status", description = f"**GDPS Count:** {gdps_count}\n" + 
                                                                            f"**GDPS Banned:** {gdps_bans}\n"
                                                                            f"**Web Server:** {apache_emoji}\n"
                                                                            f"**MySQL:** {mysql_emoji}\n" + 
                                                                            f"**FTP:** {ftp_emoji}\n" + 
                                                                            f"**API:** {api_emoji}\n\n" + 
                                                                            f"Conclusion: {conclusion}", color = discord.Colour.green())
    await ctx.send(embed=data_embed)

@client.command()
async def safestop(ctx):
    puser = is_admin(ctx.author.id, "gdpsfh")
    if puser is not True:
        await ctx.send("no")
        return
    cursor = execute_sql("update gdps_creator_config set lockdown_status = 1 where id = 'gdpsfh'")
    cursor = execute_sql("update gdps_creator_config set lockdown_status = 1 where id = 'gdpsfhru'")
    setup_count = len(currently_creating)
    if len(in_setup) != 0:
        embed = discord.Embed(title="<a:loading:762295133747413022> Waiting for current gdps creation process to finish...", color = discord.Colour.green())
        waiting = await ctx.send(embed=embed)
        while True:
            if len(in_setup) == 0:
                break
            await asyncio.wait(1)
        await waiting.delete()
    if setup_count != 0:
        embed = discord.Embed(title=f"<a:loading:762295133747413022> Notifying {setup_count} users currently in setup...", color = discord.Colour.green())
        waiting = await ctx.send(embed=embed)
        for ids in currently_creating:
            user = await client.fetch_user(ids)
            embed = discord.Embed(description="The bot has to restart so your GDPS setup has to be cancelled, try entering the ps!c command again.", color = discord.Colour.red())
            try:
                await user.send(embed=embed)
            except:
                continue
        await waiting.delete()
        embed = discord.Embed(description="All users notified, stopping the bot...", color = discord.Colour.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description="Stopping the bot...", color = discord.Colour.green())
        await ctx.send(embed=embed)
    cursor = execute_sql("update gdps_creator_config set lockdown_status = 0 where id = 'gdpsfh'")
    cursor = execute_sql("update gdps_creator_config set lockdown_status = 0 where id = 'gdpsfhru'")
    exit()
    
@client.command()
async def credits(ctx):
    embed = discord.Embed(title = "Bot informations", description = "**Owner:** MathieuAR"
                                                                  + "\n**Bot profile picture** : Robby"
                                                                  + "\n**Bot version** : 3.3", color = discord.Colour.from_rgb(255, 0, 0))
    embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/781299379491176449/820436217719291934/GDPS_Creator.png")
    await ctx.send(embed=embed)

@client.command()
async def editfile(ctx):
    if ctx.author.id != 195598321501470720:
        await ctx.send("no")
        return
    f = open("gdps", "r")
    contents = f.readlines()
    f.close()
    cursor = execute_sql("select gdps_custom_url,userID from gdps_creator_userdata")
    data = cursor.fetchall()
    for gdps_curl in data:
        if "\u0421" in gdps_curl[0] or "\u062a" in gdps_curl[0]:
            print(gdps_curl[1])
            continue
        gdps_curl = gdps_curl[0]
        value = ("    location /" + gdps_curl + " { \n"
               + "        fastcgi_param php_admin_value open_basedir=\"/var/www/gdps/" + gdps_curl + "/:/usr/share/phpmyadmin/:/usr/share/php\";\n"
               + "        location ~ \.php$ {\n"
               + "            include snippets/fastcgi-php.conf;\n"
               + "            fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;\n"
               + "            fastcgi_pass unix:/run/php/gdps/gdopenserver.sock;\n"
               + "		}\n"
               + "	}\n\n")
        contents.insert(17, value)

    f = open("gdps", "w")
    contents = "".join(contents)
    f.write(contents)
    f.close()

@client.command()
async def banwave(ctx):
    language = checklang(ctx.guild.id)
    if language is False:
        await ctx.send("An error occured with the language selector.")
        return
    lang = language[0]
    if ctx.author.id != 195598321501470720:
        embed = discord.Embed(description=getlang(f"{lang}_global_not_allowed_use_command"), color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    ban_count = 0
    wait_ban = []
    gdpsfh = client.get_guild(743013350446989442)
    gdpsfhru = client.get_guild(863435774337613834)
    #gdpshub = client.get_guild(746258756328751105)
    cursor = execute_sql("select * from gdps_creator_userdata")
    data = cursor.fetchall()
    for rows in data:
        #if gdpsfh.get_member(int(rows[0])) is None and gdpshub.get_member(int(rows[0])) is None and gdpsfhru.get_member(int(rows[0])) is None:
        if gdpsfh.get_member(int(rows[0])) is None and gdpsfhru.get_member(int(rows[0])) is None:
            if rows[5] != 1:
                ban_count += 1
                wait_ban.append(rows[0])
    if ban_count == 0:
        embed = discord.Embed(description="Every user that has a GDPS is on the server so everything is fine!", color = discord.Colour.green())
        await ctx.send(embed=embed)
        return
    else:
        embed = discord.Embed(description=f"{ban_count} users can be banned because they are not on the server anymore, do you want to ban them? (yes/no)", color = discord.Colour.orange())
        await ctx.send(embed=embed)
    confirmation = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    if confirmation.content == "yes":
        #log_channel = client.get_channel(820006114217033808)
        embed = discord.Embed(title=f"<a:loading:762295133747413022> Deleting {ban_count} GDPS please wait...", color = discord.Colour.green())
        delete_msg = await ctx.send(embed=embed)
        for ids in wait_ban:
            cursor = execute_sql("select gdps_custom_url from gdps_creator_userdata where userID = %s", [ids])
            data = cursor.fetchall()
            process = await asyncio.create_subprocess_shell(f'./DelGDPS-Bot.sh {data[0][0]}')
            await process.communicate()
            cursor = execute_sql("update gdps_creator_userdata set left_server = %s where userID = %s", [1, ids])
            #banned_member = await client.fetch_user(int(ids))
            #await log_channel.send(f"{banned_member.mention} (\"{banned_member.name}\") got his GDPS deleted with no way of creating a new one because he left the server.")
        await delete_msg.delete()
        embed = discord.Embed(title=f"Deleted {ban_count} GDPS!", color = discord.Colour.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description=f"GDPS deletion stopped!", color = discord.Colour.green())
        await ctx.send(embed=embed)

@client.command()
async def merge_to_mysql(ctx):
    if ctx.author.id != 195598321501470720:
        await ctx.send("no")
        return
    with open("user-data.json", "r+") as file:
        data = json.load(file)
        count = 0
        for ids in data:
            left_server = 0
            if data[ids]["left_server"] == "yes":
                left_server = 1
            cursor = execute_sql("insert into gdps_creator_userdata (userID, gdps_name, gdps_custom_url, gdps_version, gdps_password, left_server, moderators, on_gdps_browser) values (%s, %s, %s, %s, %s, %s, %s, %s)", [int(ids), data[ids]["gdps_name"], data[ids]["gdps_custom_url"], data[ids]["gdps_version"], data[ids]["password"], left_server, str(data[ids]["moderators"]), 0])
            count += 1
            print(f"{ids} is in the db! Number: {count}")
    
    await ctx.send("fini")

@client.command()
async def ip(ctx, option=None, value=None, *, reason=None):
    authorised_id = [195598321501470720, 180790976128745472]
    if ctx.author.id not in authorised_id:
        await ctx.send("no")
        return
    if option is None:
        await ctx.send("You need to enter an option. (ban, unban)")
        return
    if value is None:
        await ctx.send("You need to enter an ip to ban.")
        return

    if option == "ban":
        if reason is None:
            await ctx.send("You need to enter a ban reason.")
            return
        url = "https://api.cloudflare.com/client/v4/zones/01e41405b861ae12ebde1ffa69ee4dee/firewall/access_rules/rules"
        headers = {"X-Auth-Email": cloudflare_email,
                   "X-Auth-Key": cloudflare_api_key,
                   "Content-type": "application/json"}
        req_data = {"mode": "block",
                    "configuration": {"target": "ip",
                                      "value": value},
                    "notes": reason}
        try:
            req = requests.post(url, data=json.dumps(req_data), headers=headers, timeout=5)
        except Exception as e:
            print(e)
            await ctx.send("An error occured with the cloudflare api.")
            return
        req = req.json()
        if req["success"]:
            await ctx.send("IP banned!")
        else:
            error = req["errors"]
            if error[0]["message"] == "firewallaccessrules.api.duplicate_of_existing":
                await ctx.send("This ip is already banned.")
                return
            await ctx.send(f"There was an error with cloudflare.\n\nError: {error}")
    elif option == "unban":
        url = f"https://api.cloudflare.com/client/v4/zones/01e41405b861ae12ebde1ffa69ee4dee/firewall/access_rules/rules?configuration.target=ip&configuration.value={value}&mode=block"
        headers = {"X-Auth-Email": "mathieu.maik.15@gmail.com",
                   "X-Auth-Key": "e6b8a4d07f78528eeba55fa502a92424abe06",
                   "Content-type": "application/json"}
        try:
            req = requests.get(url, headers=headers, timeout=5)
        except Exception as e:
            print(e)
            await ctx.send("An error occured with the cloudflare api.")
            return
        req = req.json()
        if not req["success"]:
            error = req["errors"]
            await ctx.send(f"There was an error with cloudflare.\n\nError: {error}")
            return
        if len(req["result"]) == 0:
            await ctx.send("This IP isn't banned.")
            return
        elif len(req["result"]) > 1:
            await ctx.send("2 IPS matched cancelled the unban, please contact MathieuAR.")
            return
        access_rule_id = req["result"][0]["id"]
        url = f"https://api.cloudflare.com/client/v4/zones/01e41405b861ae12ebde1ffa69ee4dee/firewall/access_rules/rules/{access_rule_id}"
        try:
            req = requests.delete(url, headers=headers, timeout=5)
        except Exception as e:
            print(e)
            await ctx.send("An error occured with the cloudflare api.")
            return
        req=req.json()
        if req["success"]:
            await ctx.send("IP unbanned!")
        else:
            error = req["result"]["errors"]
            await ctx.send(f"There was an error with cloudflare.\n\nError: {error}")
            return
    else:
        await ctx.send("Invalid option.")
        return

def checklang(serverid):
    if serverid == 743013350446989442:
        return "en", "gdpsfh"
    elif serverid == 863435774337613834:
        return "ru", "gdpsfhru"
    elif serverid == 746258756328751105:
        return "en", "gdpshub"
    else:
        return False

def getlang(lang):
    return os.environ.get(lang)

async def in_right_channel(ctx):
    valid_channels = [820747188623114252, #GDPSFH - gdps creator commands
                      797900335070183474, #GDPSFH - test bot
                      746465799870611557, #GDPSFH - staff bot
                      866691253114765322, #GDPS Hub - gdps creator commands
                      863435775428919337] #GDPSFH RU - gdps creator commands
    if ctx.channel.id not in valid_channels and ctx.author.id != 195598321501470720:
        embed = discord.Embed(description=f"This command can only be used in the <#820747188623114252> channel", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return False
    return True

async def command_cooldown(ctx, userid, cooldown_name, cooldown_time):
    userid = str(userid)
    with open("on_cooldown.json", "r+") as file:
        data = json.load(file)
        file.seek(0)
        current_time = time.time_ns() // 1_000_000
        if userid in str(data):
            is_exist = data[userid].get(cooldown_name, "null")
            if is_exist != "null":
                old_cooldown_time = data[userid][cooldown_name]
                if current_time < old_cooldown_time:
                    time_substract = old_cooldown_time-current_time
                    hour = int(datetime.fromtimestamp(time_substract/1000).strftime("%H"))
                    real_hour = hour-1
                    transformed_time = datetime.fromtimestamp(time_substract/1000).strftime("%M Minutes and %S Seconds")
                    if "00 Minutes" in transformed_time:
                        time_substract = old_cooldown_time-current_time
                        transformed_time = datetime.fromtimestamp(time_substract/1000).strftime("%S Seconds")
                    if real_hour > 0:
                        if real_hour == 1:
                            embed = discord.Embed(title=f"This command is on cooldown, please try again in {real_hour} Hour {transformed_time}.", color = discord.Colour.red())
                            await ctx.send(embed=embed)
                            return True
                        else:
                            embed = discord.Embed(title=f"This command is on cooldown, please try again in {real_hour} Hours {transformed_time}.", color = discord.Colour.red())
                            await ctx.send(embed=embed)
                            return True
                    else:
                        embed = discord.Embed(title=f"This command is on cooldown, please try again in {transformed_time}.", color = discord.Colour.red())
                        await ctx.send(embed=embed)
                        return True
                else:
                    updated_time = current_time + cooldown_time
                    data[userid][cooldown_name] = updated_time
                    json.dump(data, file, indent=4)
                    return False
            else:
                updated_time = current_time + cooldown_time
                data[userid][cooldown_name] = updated_time
                json.dump(data, file, indent=4)
                return False
        else:
            updated_time = current_time + cooldown_time
            data[userid] = {cooldown_name: updated_time}
            json.dump(data, file, indent=4)
            return False

def has_gdps(user_id):
    cursor = execute_sql("select userID from gdps_creator_userdata where userID = %s", [user_id])
    if cursor.rowcount == 0:
        return False
    return True

def is_admin(user_id, server_config):
    cursor = execute_sql("select authorised_users from gdps_creator_config where id = %s", [server_config])
    data = cursor.fetchall()
    if str(user_id) in str(data):
        return True
    else:
        return False

async def check_donator(ctx, gdpsowner=None):
    if gdpsowner is not None:
        for rid in donator_roles:
            if str(rid) in str(gdpsowner.roles):
                return True
        embed = discord.Embed(description=f"This command is a premium feature, it can only be used if the GDPS owner is a server boosters or a donator.", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return False
    else:
        for rid in donator_roles:
            if str(rid) in str(ctx.author.roles):
                return True
        embed = discord.Embed(description=f"This command is a premium feature, it can only be used by server boosters or donators.", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return False

def execute_sql(command, values=None):
    connection.ping(reconnect=True)
    cursor.execute(command, values)
    return cursor

@client.event
async def on_ready():
    print("Bot chargé")

client.run(bot_token)