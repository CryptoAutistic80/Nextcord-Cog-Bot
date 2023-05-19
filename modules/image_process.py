from PIL import Image  # Importing the Image class from the PIL library
from datetime import datetime  # Importing the datetime module for working with dates and times
import urllib.request  # Importing the urllib.request module for working with URLs and making HTTP requests

def stitch_images(response):
    # Array to store image files
    image_files = []

    for idx, img in enumerate(response['data']):
        image_url = img['url']
        print(image_url)

        # Save the images in the new_images directory
        file_name = "new_images/image" + datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + f"_{idx}.png"
        urllib.request.urlretrieve(image_url, file_name)
        image_files.append(file_name)

    # Open images and resize if necessary
    imgs = [Image.open(i) for i in image_files]

    # Create a new image of size 2x2 of the input images
    collage_image = Image.new('RGB', (imgs[0].width * 2, imgs[0].height * 2))
    collage_image.paste(imgs[0], (0, 0))
    collage_image.paste(imgs[1], (imgs[0].width, 0))
    collage_image.paste(imgs[2], (0, imgs[0].height))
    collage_image.paste(imgs[3], (imgs[0].width, imgs[0].height))

    # Save the collage image
    file_to_send = "new_images/collage" + datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + ".png"
    collage_image.save(file_to_send)

    return file_to_send, image_files


