import os
from PIL import Image
from datetime import datetime
import urllib.request

def stitch_images(response):
    image_files = []

    for idx, img in enumerate(response['data']):
        image_url = img['url']

        file_name = "ai_resources/new_images/image" + datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + f"_{idx}.png"
        urllib.request.urlretrieve(image_url, file_name)
        image_files.append(file_name)

    imgs = [Image.open(i) for i in image_files]

    collage_image = Image.new('RGB', (imgs[0].width * 2, imgs[0].height * 2))
    collage_image.paste(imgs[0], (0, 0))
    collage_image.paste(imgs[1], (imgs[0].width, 0))
    collage_image.paste(imgs[2], (0, imgs[0].height))
    collage_image.paste(imgs[3], (imgs[0].width, imgs[0].height))

    file_to_send = "ai_resources/new_images/collage" + datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + ".png"
    collage_image.save(file_to_send)

    return file_to_send, image_files

def process_image(image_path):
    img = Image.open(image_path)

    if img.width != img.height:
        min_size = min(img.width, img.height)
        img = img.crop(
            (
                (img.width - min_size) // 2,
                (img.height - min_size) // 2,
                (img.width + min_size) // 2,
                (img.height + min_size) // 2
            )
        )

    if img.format != 'PNG':
        image_path = image_path.rsplit('.', 1)[0] + '.png'
        img.save(image_path)

    max_size = 1024
    if max(img.width, img.height) > max_size:
        if img.width > img.height:
            new_width = max_size
            new_height = int(max_size * img.height / img.width)
        else:
            new_height = max_size
            new_width = int(max_size * img.width / img.height)
        img = img.resize((new_width, new_height))
        img.save(image_path)

    while os.path.getsize(image_path) > 4 * 1024 * 1024:
        img = Image.open(image_path)
        img.save(image_path, optimize=True, quality=50)

    return image_path


