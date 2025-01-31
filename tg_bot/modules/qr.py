import os
from asyncio import sleep
from datetime import datetime
from requests import get, post
from tg_bot.events import register


def progress(current, total):
    """ Calculate and return the download progress with given arguments. """
    print("Downloaded {} of {}\nCompleted {}".format(current, total,
                                                     (current / total) * 100))


@register(pattern=r"^/getqr$")
async def parseqr(qr_e):
    """ For .getqr command, get QR Code content from the replied photo. """
    if qr_e.fwd_from:
        return
    start = datetime.now()
    downloaded_file_name = await qr_e.client.download_media(
        await qr_e.get_reply_message(), progress_callback=progress)
    url = "https://api.qrserver.com/v1/read-qr-code/?outputformat=json"
    with open(downloaded_file_name, "rb") as file:
        files = {"file": file}
        resp = post(url, files=files).json()
        qr_contents = resp[0]["symbol"][0]["data"]
    os.remove(downloaded_file_name)
    end = datetime.now()
    duration = (end - start).seconds
    await qr_e.reply("Obtained QRCode contents in {} seconds.\n{}".format(
        duration, qr_contents))


@register(pattern=r"^/makeqr(?: |$)([\s\S]*)")
async def make_qr(qrcode):
    """ For .makeqr command, make a QR Code containing the given content. """
    if qrcode.fwd_from:
        return
    start = datetime.now()
    input_str = qrcode.pattern_match.group(1)
    message = "SYNTAX: `.makeqr <long text to include>`"
    reply_msg_id = None
    if input_str:
        message = input_str
    elif qrcode.reply_to_msg_id:
        previous_message = await qrcode.get_reply_message()
        reply_msg_id = previous_message.id
        if previous_message.media:
            downloaded_file_name = await qrcode.client.download_media(
                previous_message, progress_callback=progress)
            m_list = None
            with open(downloaded_file_name, "rb") as file:
                m_list = file.readlines()
            message = "".join(media.decode("UTF-8") + "\r\n" for media in m_list)
            os.remove(downloaded_file_name)
        else:
            message = previous_message.message

    url = "https://api.qrserver.com/v1/create-qr-code/?data={}&\
size=200x200&charset-source=UTF-8&charset-target=UTF-8\
&ecc=L&color=0-0-0&bgcolor=255-255-255\
&margin=1&qzone=0&format=jpg"

    resp = get(url.format(message), stream=True)
    required_file_name = "temp_qr.webp"
    with open(required_file_name, "w+b") as file:
        for chunk in resp.iter_content(chunk_size=128):
            file.write(chunk)
    await qrcode.client.send_file(
        qrcode.chat_id,
        required_file_name,
        reply_to=reply_msg_id,
        progress_callback=progress,
    )
    os.remove(required_file_name)
    duration = (datetime.now() - start).seconds
    await qrcode.reply("Created QRCode in {} seconds".format(duration))
    await sleep(5)

__help__ = """
 - /getqr: Get the QR Code content from the replied QR Code
 - /makeqr <content>: Make a QR Code from the given message (text, link, etc...)
"""
__mod_name__ = "QR code"
