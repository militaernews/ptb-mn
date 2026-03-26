from pywa import WhatsApp, types

# Create a WhatsApp client
wa = WhatsApp(
    phone_id="100458559237541",
    token="EAAEZC6hUxkTIB"
)

# Send a text message with buttons
wa.send_message(
    to="9876543210",
    text="Hello from PyWa!",
    buttons=[
        types.Button(title="Menu", callback_data="menu"),
        types.Button(title="Help", callback_data="help")
    ]
)

# Send a image message from URL
wa.send_image(
    to="9876543210",
    image="https://example.com/image.jpg",
    caption="Check out this image!",
)