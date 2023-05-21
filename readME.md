# Discord Bot User Guide / Readme

This guide provides an overview of the functionality and usage instructions for the Discord bot implemented with the provided `.py` files.

## Files Included

The following `.py` files are included:

1. `main.py`: This file contains the main code for initializing and running the Discord bot. It handles the bot's setup, event handling, and command execution.

2. `chat.py`: This file implements a chat functionality for the Discord bot. It allows users to have interactive conversations with the bot using the `/chat` command.

3. `eightball.py`: This file implements a Magic 8-Ball functionality for the Discord bot. Users can ask questions to the Magic 8-Ball using the `/magic8ball` command.

4. `paint.py`: This file implements a painting functionality for the Discord bot. It allows users to generate and manipulate images based on text prompts or uploaded images.

5. `ping.py`: This file implements a ping functionality for the Discord bot. Users can ping the bot and receive a response with the bot's latency.

## Usage Instructions

1. **Setting Up the Environment**:

   - Make sure you have the necessary Python dependencies installed. You can use the `pip install` command to install the required dependencies specified in each `.py` file.

   - Set up the required environment variables for the Discord bot and the OpenAI API key. Refer to the respective `.py` files to determine the required environment variables.

2. **Running the Discord Bot**:

   - Run the `main.py` file to start the Discord bot. Make sure the environment variables are correctly set before running the file.

3. **Interacting with the Bot**:

   - Once the bot is running, you can interact with it on Discord.

   - To use the chat functionality, use the `/chat` command. For example, `/chat Hello, bot!` initiates a conversation with the bot.

   - To use the Magic 8-Ball functionality, use the `/magic8ball` command. For example, `/magic8ball Will it rain tomorrow?` asks the Magic 8-Ball a question.

   - To use the painting functionality, there are two options:

     - Use the `/paint` command with a text prompt to generate an image. For example, `/paint "A beautiful sunset" --resolution 512x512` generates an image based on the prompt.

     - Use the `/upload` command to upload an image and generate variations. For example, `/upload --resolution 1024x1024` allows you to upload an image and generate variations based on the resolution.

   - To ping the bot, use the `/ping` command. For example, `/ping` pings the bot and displays the bot's latency.

4. **Interacting with Buttons**:

   - Some functionalities include interactive buttons for user interaction.

   - In the chat functionality, you will find an "End" button to end the conversation.

   - In the painting functionality, you will find buttons for image selection, regeneration, and variation. These buttons allow you to navigate and manipulate the generated images.

5. **Further Customization**:

   - You can modify the functionality and behavior of the bot by editing the respective `.py` files according to your requirements.

That's it! You now have a Discord bot with multiple functionalities at your disposal. Enjoy interacting with the bot and exploring its features!

Please note that this is a basic user guide, and you may need to refer to the individual `.py` files for more detailed information or customization options.
