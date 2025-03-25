import discord
from discord.ext import commands
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

# Command to add an item to the marketplace
@bot.command(name='additem', help='Add an item to the marketplace')
async def add_item(ctx, title: str, description: str, price: float):
    # Check if the user attached an image
    if not ctx.message.attachments:
        await ctx.send("Please attach an image with your item.")
        return

    # Get the first attached image
    image = ctx.message.attachments[0]
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
        'seller': ctx.author.name,
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
    await ctx.send(embed=embed)

# Command to list all items in the marketplace
@bot.command(name='listitems', help='List all items in the marketplace')
async def list_items(ctx):
    items = load_items()
    if not items['items']:
        await ctx.send("No items are currently available in the marketplace.")
        return

    # Create an embed for each item
    for item in items['items']:
        embed = discord.Embed(title=item['title'], description=item['description'], color=discord.Color.blue())
        embed.add_field(name="Price", value=f"${item['price']}", inline=False)
        embed.add_field(name="Seller", value=item['seller'], inline=False)
        embed.set_image(url=item['image_url'])
        await ctx.send(embed=embed)

# Command to search for items
@bot.command(name='search', help='Search for items by keyword')
async def search_items(ctx, keyword: str):
    items = load_items()
    found_items = [item for item in items['items'] if keyword.lower() in item['title'].lower() or keyword.lower() in item['description'].lower()]

    if not found_items:
        await ctx.send("No items found matching your search.")
        return

    for item in found_items:
        embed = discord.Embed(title=item['title'], description=item['description'], color=discord.Color.blue())
        embed.add_field(name="Price", value=f"${item['price']}", inline=False)
        embed.add_field(name="Seller", value=item['seller'], inline=False)
        embed.set_image(url=item['image_url'])
        await ctx.send(embed=embed)

# Command to remove an item from the marketplace
@bot.command(name='removeitem', help='Remove an item from the marketplace')
async def remove_item(ctx, item_id: int):
    items = load_items()
    try:
        item = next(item for item in items['items'] if item['id'] == item_id)
        if item['seller'] == ctx.author.name:
            items['items'].remove(item)
            save_items(items)
            await ctx.send("Item removed successfully.")
        else:
            await ctx.send("You don't have permission to remove this item.")
    except StopIteration:
        await ctx.send("Item not found.")

# Run the bot with token from environment variable
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("Error: DISCORD_TOKEN not found in environment variables")
    exit(1)
bot.run(token)