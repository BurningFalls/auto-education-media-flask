import requests


async def generate_image(text, client):
    dalle_response = await client.images.generate(
        model="dall-e-3",
        prompt=text,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = dalle_response.data[0].url
    image_response = requests.get(image_url)

    return image_response.content
