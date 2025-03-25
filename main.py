
import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image
import json
import os

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
    except Exception as e:
        print(e)

# Command to add an item to the marketplace
@bot.tree.command(name='additem', description='Add an item to the marketplace')
@app_commands.describe(
    title="The title of your item",
    description="A description of your item",
    price="The price of your item"
)
async def add_item(interaction: discord.Interaction, title: str, description: str, price: float):
    # Check if the user attached an image
    if not interaction.message.attachments:
        await interaction.response.send_message("Please attach an image with your item.", ephemeral=True)
        return

    # Get the first attached image
    image = interaction.message.attachments[0]
    image_url = image.url
    image_path = f"item_images/{image.filename}"

    # Save the image locally
    await image.save(image_path)

    # Generate a unique ID for the item
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

    # Send a confirmation message
    embed = discord.Embed(title="Item Added!", description=f"Item ID: {item_id}", color=discord.Color.green())
    embed.add_field(name="Title", value=title, inline=False)
    embed.add_field(name="Description", value=description, inline=False)
    embed.add_field(name="Price", value=f"${price}", inline=False)
    embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='listitems', description='List all items in the marketplace')
async def list_items(interaction: discord.Interaction):
    items = load_items()
    if not items['items']:
        await interaction.response.send_message("No items are currently available in the marketplace.", ephemeral=True)
        return

    # Create an embed for each item
    await interaction.response.send_message("Here are the available items:", ephemeral=True)
    for item in items['items']:
        embed = discord.Embed(title=item['title'], description=item['description'], color=discord.Color.blue())
        embed.add_field(name="Price", value=f"${item['price']}", inline=False)
        embed.add_field(name="Seller", value=item['seller'], inline=False)
        embed.set_image(url=item['image_url'])
        await interaction.followup.send(embed=embed)

@bot.tree.command(name='search', description='Search for items by keyword')
@app_commands.describe(keyword="The keyword to search for")
async def search_items(interaction: discord.Interaction, keyword: str):
    items = load_items()
    found_items = [item for item in items['items'] if keyword.lower() in item['title'].lower() or keyword.lower() in item['description'].lower()]

    if not found_items:
        await interaction.response.send_message("No items found matching your search.", ephemeral=True)
        return

    await interaction.response.send_message(f"Found {len(found_items)} items matching '{keyword}':", ephemeral=True)
    for item in found_items:
        embed = discord.Embed(title=item['title'], description=item['description'], color=discord.Color.blue())
        embed.add_field(name="Price", value=f"${item['price']}", inline=False)
        embed.add_field(name="Seller", value=item['seller'], inline=False)
        embed.set_image(url=item['image_url'])
        await interaction.followup.send(embed=embed)

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
