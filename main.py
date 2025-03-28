import discord
from discord.ext import commands
from discord import app_commands
import json
import os
# love
# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Create a folder to store item images
if not os.path.exists('item_images'):
    os.makedirs('item_images')

# Load or create an items database
def load_items():
    if os.path.exists('items.json'):
        with open('items.json', 'r') as f:
            return json.load(f)
    else:
        return {'items': []}

def save_items(items):
    with open('items.json', 'w') as f:
        json.dump(items, f, indent=4)

# Event to indicate the bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
        await bot.change_presence(activity=discord.Game(name="Join discord.gg/boosttik for TikTok shop accounts"))
    except Exception as e:
        print(e)

# Command to add an item to the marketplace
@bot.tree.command(name='additem', description='Add an item to the marketplace')
@app_commands.describe(
    title="The title of your item",
    description="A description of your item",
    price="The price of your item",
    attachment="The image of your item"
)
async def add_item(interaction: discord.Interaction, title: str, description: str, price: float, attachment: discord.Attachment):
    if not attachment.content_type.startswith('image/'):
        await interaction.response.send_message("Please provide a valid image file.", ephemeral=True)
        return

    image = attachment
    image_url = image.url
    image_path = f"item_images/{image.filename}"

    await image.save(image_path)

    items = load_items()
    item_id = len(items['items']) + 1
    new_item = {
        'id': item_id,
        'title': title,
        'description': description,
        'price': price,
        'image_url': image_url,
        'seller': interaction.user.name,
        'image_path': image_path
    }

    items['items'].append(new_item)
    save_items(items)

    embed = discord.Embed(title="New Account!", description=f"Item ID: {item_id}", color=discord.Color.blue())
    embed.add_field(name="Title", value=title, inline=False)
    embed.add_field(name="Description", value=description, inline=False)
    embed.add_field(name="Price", value=f"${price}", inline=False)
    embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed)

# Add this near the top of the file, after the imports
user_purchase_cooldowns = {}

@bot.tree.command(name='listitems', description='List all items in the marketplace')
async def list_items(interaction: discord.Interaction):
    items = load_items()
    if not items['items']:
        await interaction.response.send_message("No items are currently available in the marketplace.", ephemeral=True)
        return

    await interaction.response.send_message("Here are the available items:", ephemeral=True)
    for item in items['items']:
        embed = discord.Embed(title=item['title'], description=item['description'], color=discord.Color.blue())
        embed.add_field(name="Price", value=f"${item['price']}", inline=False)
        embed.add_field(name="Seller", value=item['seller'], inline=False)
        embed.set_image(url=item['image_url'])

        button = discord.ui.Button(label="Purchase", style=discord.ButtonStyle.green, custom_id=f"purchase_{item['id']}")

        async def button_callback(interaction: discord.Interaction, item_id=item['id']):  # Closure to capture item_id
            # Check if user is on cooldown
            current_time = discord.utils.utcnow()
            user_id = interaction.user.id

            if user_id in user_purchase_cooldowns:
                last_purchase_time = user_purchase_cooldowns[user_id].get(item_id)
                if last_purchase_time:
                    # 1 hour cooldown between purchases for the same item
                    if (current_time - last_purchase_time).total_seconds() < 3600:
                        await interaction.response.send_message(
                            "You can only purchase this item once per hour. Please wait before trying again.", 
                            ephemeral=True
                        )
                        return

            # Create purchase channel
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True)
            }
            purchase_channel = await guild.create_text_channel(f"purchase-{item_id}", overwrites=overwrites)

            # Update cooldown tracking
            if user_id not in user_purchase_cooldowns:
                user_purchase_cooldowns[user_id] = {}
            user_purchase_cooldowns[user_id][item_id] = current_time

            # Create a view with a close channel button
            close_view = discord.ui.View()
            close_button = discord.ui.Button(label="Close Channel", style=discord.ButtonStyle.red, custom_id=f"close_channel_{purchase_channel.id}")

            async def close_channel_callback(close_interaction: discord.Interaction):
                # Check if the user has permissions to close the channel
                if close_interaction.user.guild_permissions.manage_channels:
                    await purchase_channel.delete()
                else:
                    await close_interaction.response.send_message("You don't have permission to close this channel.", ephemeral=True)

            close_button.callback = close_channel_callback
            close_view.add_item(close_button)

            # Log who opened the private channel
            log_channel = discord.utils.get(guild.text_channels, name="logs")
            if log_channel:
                await log_channel.send(f"{interaction.user.name} opened a private channel for item ID {item_id}.")

            await purchase_channel.send(f"@everyone Please wait until staff replies.\nPayment Method:", view=close_view)
            await interaction.response.send_message(f"Private channel created for item ID {item_id}.", ephemeral=True)

        button.callback = button_callback

        view = discord.ui.View()
        view.add_item(button)

        await interaction.followup.send(embed=embed, view=view)

@bot.tree.command(name='removeitem', description='Remove an item from the marketplace')
@app_commands.describe(item_id="The ID of the item to remove")
async def remove_item(interaction: discord.Interaction, item_id: int):
    items = load_items()
    try:
        item = next(item for item in items['items'] if item['id'] == item_id)
        if item['seller'] == interaction.user.name:
            items['items'].remove(item)
            save_items(items)
            await interaction.response.send_message("Item removed successfully.", ephemeral=True)
        else:
            await interaction.response.send_message("You don't have permission to remove this item.", ephemeral=True)
    except StopIteration:
        await interaction.response.send_message("Item not found.", ephemeral=True)

# Run the bot with token from environment variable
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("Error: DISCORD_TOKEN not found in environment variables")
    exit(1)
bot.run(token)