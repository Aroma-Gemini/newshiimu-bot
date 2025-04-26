import discord
from discord.ext import commands, tasks
import asyncio
import random
import os

# 役割と色の設定
roles = {
    "デュエリスト": 0xFF0000,    # 赤
    "イニシエーター": 0x00FF00,  # 緑
    "コントローラー": 0x0000FF,  # 青
    "センチネル": 0xFFFF00,     # 黄
    "フレックス": 0x808080       # グレー
}

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 監視中チャンネルリスト
watch_channels = set()

# メッセージ記録 {message_id: (message_object, timestamp)}
message_records = {}

class StartView(discord.ui.View):
    def __init__(self, members, specified_count):
        super().__init__(timeout=None)
        self.members = members
        self.specified_count = specified_count

    @discord.ui.button(label="🎲START🎲", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.specified_count > len(self.members):
            await interaction.response.send_message("人数が合わないよ！", ephemeral=True)
            return

        selected_members = random.sample(self.members, self.specified_count)

        if self.specified_count == 1:
            assigned_roles = ["フレックス"]
        elif self.specified_count in [2,3,4]:
            assigned_roles = random.sample(list(roles.keys())[:-1], self.specified_count)
        elif self.specified_count == 5:
            assigned_roles = list(roles.keys())
        elif 6 <= self.specified_count <= 9:
            await interaction.response.send_message("プレイ出来る人数ではありません", ephemeral=True)
            return
        elif self.specified_count == 10:
            team_a = random.sample(selected_members, 5)
            team_b = [m for m in selected_members if m not in team_a]
            embed_a = discord.Embed(title="Aチーム", color=0x00FFFF)
            embed_b = discord.Embed(title="Bチーム", color=0xFF00FF)
            for member in team_a:
                role = random.choice(list(roles.keys()))
                embed_a.add_field(name=member.display_name, value=role, inline=False)
            for member in team_b:
                role = random.choice(list(roles.keys()))
                embed_b.add_field(name=member.display_name, value=role, inline=False)
            await interaction.response.send_message(embeds=[embed_a, embed_b])
            return
        elif self.specified_count > 10:
            await interaction.response.send_message("人数が多すぎます", ephemeral=True)
            return

        embed = discord.Embed(title="役割割り振り結果", color=0xFFFFFF)
        for member, role in zip(selected_members, assigned_roles):
            embed.add_field(name=member.display_name, value=f"{role}", inline=False)
            embed.color = roles[role]
        await interaction.response.send_message(embed=embed)

class SelectNumberView(discord.ui.View):
    def __init__(self, members):
        super().__init__(timeout=None)
        self.members = members

    @discord.ui.select(
        placeholder="人数を選んでください",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label=str(i), value=str(i)) for i in range(1, 11)
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        specified_count = int(select.values[0])
        view = StartView(self.members, specified_count)
        await interaction.response.send_message("人数がセットされたよ！STARTを押してね！", view=view)

@bot.command()
async def shiimu(ctx):
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        await ctx.send("ボイスチャンネルに参加してから使ってね！")
        return

    voice_channel = ctx.author.voice.channel
    members = [member for member in voice_channel.members if not member.bot]

    view = SelectNumberView(members)
    await ctx.send("人数を選んでね！", view=view)

@bot.command()
async def delete(ctx):
    options = [discord.SelectOption(label=channel.name, value=str(channel.id)) for channel in ctx.guild.text_channels]

    class ChannelSelectView(discord.ui.View):
        @discord.ui.select(placeholder="監視するチャンネルを選んでね！", options=options)
        async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
            channel_id = int(select.values[0])
            watch_channels.add(channel_id)
            await interaction.response.send_message(f"<#{channel_id}> を監視するように設定したよ！")

    await ctx.send("チャンネルを選んでね！", view=ChannelSelectView())

@bot.command()
async def alldelete(ctx):
    options = [discord.SelectOption(label=channel.name, value=str(channel.id)) for channel in ctx.guild.text_channels]

    class ChannelSelectView(discord.ui.View):
        @discord.ui.select(placeholder="一括削除するチャンネルを選んでね！", options=options)
        async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
            channel_id = int(select.values[0])
            channel = ctx.guild.get_channel(channel_id)
            deleted_count = 0
            async for message in channel.history(limit=100):
                if message.id in message_records:
                    msg_obj, timestamp = message_records[message.id]
                    if discord.utils.utcnow().timestamp() - timestamp >= 86400:
                        await message.delete()
                        deleted_count += 1
            await interaction.response.send_message(f"{deleted_count}件の24時間超えメッセージを削除したよ！")

    await ctx.send("チャンネルを選んでね！", view=ChannelSelectView())

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return
    if message.channel.id in watch_channels:
        message_records[message.id] = (message, message.created_at.timestamp())
        asyncio.create_task(delete_message_later(message))

async def delete_message_later(message):
    await asyncio.sleep(86400)  # 24時間
    try:
        await message.delete()
        message_records.pop(message.id, None)
    except discord.NotFound:
        pass

bot.run(os.getenv("DISCORD_TOKEN"))
