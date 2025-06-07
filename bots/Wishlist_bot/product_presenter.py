import logging
import discord
import asyncio
import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random

logger = logging.getLogger('wishlist_bot.product_presenter')

class ProductPresenter:
    """Presents products in a visually appealing way in Discord"""
    
    def __init__(self, bot, channel_id):
        """
        Initialize the product presenter
        
        Args:
            bot: Discord bot instance
            channel_id: Discord channel ID to post messages
        """
        self.bot = bot
        self.channel_id = channel_id
        logger.info("Initializing Product Presenter")
    
    async def present_product(self, product, channel=None):
        """
        Present a product in Discord
        
        Args:
            product: Product dictionary with name, description, price, url, image_url
            channel: Discord channel to send to (optional, uses default if None)
        """
        try:
            if not channel:
                channel = self.bot.get_channel(self.channel_id)
                if not channel:
                    logger.error(f"Channel not found: {self.channel_id}")
                    return
            
            logger.info(f"Presenting product: {product.get('name', 'Unknown Product')}")
            
            # Create embedded message
            embed = discord.Embed(
                title=product.get('name', 'Interesting Product'),
                description=product.get('description', 'No description available'),
                color=discord.Color.blue(),
                url=product.get('url', 'https://example.com')
            )
            
            # Add price field
            embed.add_field(
                name="Price", 
                value=product.get('price', 'Price not available'),
                inline=True
            )
            
            # Add interest field if available
            if 'interest' in product:
                embed.add_field(
                    name="Related to", 
                    value=product.get('interest'),
                    inline=True
                )
            
            # Add image if available
            image_url = product.get('image_url')
            if image_url:
                # Check if the image URL is valid
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.head(image_url) as response:
                            if response.status == 200:
                                embed.set_image(url=image_url)
                            else:
                                # If image URL is invalid, generate a fallback image
                                logger.warning(f"Invalid image URL: {image_url}")
                                image = await self._generate_product_image(product.get('name', 'Product'))
                                embed.set_image(url="attachment://product.png")
                                await channel.send(embed=embed, file=image)
                                return
                except Exception as e:
                    logger.error(f"Error validating image URL: {e}")
                    # Generate fallback image
                    image = await self._generate_product_image(product.get('name', 'Product'))
                    embed.set_image(url="attachment://product.png")
                    await channel.send(embed=embed, file=image)
                    return
            else:
                # Generate a product image
                image = await self._generate_product_image(product.get('name', 'Product'))
                embed.set_image(url="attachment://product.png")
                await channel.send(embed=embed, file=image)
                return
            
            # Send the embed
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error presenting product: {e}")
            
            # Send a simple fallback message
            try:
                product_name = product.get('name', 'Interesting Product')
                product_desc = product.get('description', 'No description available')
                product_price = product.get('price', 'Price not available')
                product_url = product.get('url', 'https://example.com')
                
                fallback_message = f"**{product_name}**\n{product_desc}\nPrice: {product_price}\n{product_url}"
                await channel.send(fallback_message)
            except Exception as fallback_error:
                logger.error(f"Error sending fallback message: {fallback_error}")
    
    async def _generate_product_image(self, product_name):
        """
        Generate a simple product image
        
        Args:
            product_name: Name of the product
            
        Returns:
            discord.File: Discord file for the image
        """
        try:
            # Create a simple image with the product name
            width, height = 800, 400
            image = Image.new('RGB', (width, height), self._get_random_color())
            
            # Draw on the image
            draw = ImageDraw.Draw(image)
            
            # Add some decorative elements
            for i in range(10):
                x1 = random.randint(0, width)
                y1 = random.randint(0, height)
                x2 = random.randint(0, width)
                y2 = random.randint(0, height)
                draw.line((x1, y1, x2, y2), fill=self._get_random_color(), width=3)
            
            # Add product name text
            try:
                # Try to load a system font (fallback to default if not available)
                font = ImageFont.truetype("arial.ttf", 40)
            except Exception:
                font = ImageFont.load_default()
                
            # Wrap text
            wrapped_text = self._wrap_text(product_name, font, width - 40)
            
            # Position text
            text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
            text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw text with shadow for better visibility
            draw.multiline_text((x+3, y+3), wrapped_text, font=font, fill="black", align="center")
            draw.multiline_text((x, y), wrapped_text, font=font, fill="white", align="center")
            
            # Convert to file
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            
            return discord.File(buffer, filename="product.png")
            
        except Exception as e:
            logger.error(f"Error generating product image: {e}")
            
            # Return a very simple fallback image
            try:
                width, height = 400, 200
                image = Image.new('RGB', (width, height), (70, 130, 180))
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                draw.text((20, height//2), "Product Visualization", font=font, fill="white")
                
                buffer = BytesIO()
                image.save(buffer, format="PNG")
                buffer.seek(0)
                
                return discord.File(buffer, filename="product.png")
            except Exception as fallback_error:
                logger.error(f"Error creating fallback image: {fallback_error}")
                return None
    
    def _get_random_color(self):
        """Generate a random color"""
        r = random.randint(0, 200)
        g = random.randint(0, 200)
        b = random.randint(0, 200)
        return (r, g, b)
    
    def _wrap_text(self, text, font, max_width):
        """Wrap text to fit within a specified width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            # Check width of current line + new word
            test_line = ' '.join(current_line + [word])
            w = font.getbbox(test_line)[2] if hasattr(font, 'getbbox') else font.getsize(test_line)[0]
            
            if w <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines) 