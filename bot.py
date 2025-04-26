import discord
from discord.ext import commands
import random

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

bot = commands.Bot(command_prefix='!', intents=intents)

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

import os
bot.run(os.getenv(\"DISCORD_TOKEN\"))
