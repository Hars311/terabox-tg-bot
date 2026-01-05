BOT_TOKEN = "8148103361:AAG5yQeRhp5oIbpo8mDVqcoY4c6LVmAho40"

import os, requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8148103361:AAG5yQeRhp5oIbpo8mDVqcoY4c6LVmAho40"
TERABOX_COOKIE = "browserid=rkfhGXQURT8dKo9mw8KV2WhQUFHtZF4Dsww0OkOH_8vXHQr_12sTs0EM9kE=; lang=en; TSID=6GjvE4DXGJynFsNsxU6pxeiJjvy5rty9; __bid_n=19b8d74d542600bbdc4207; ndus=YyVskB9peHui-OkBnqSF5YzZuReuuw2MFRKQ5_vZ; csrfToken=eRRjJyhAYIjiKK44nNP0ZX7f; __stripe_mid=6be9a5eb-f915-4e67-882a-5ba16969e4561f9f60; __stripe_sid=16bc9bde-123b-49ec-90e9-be3619da8026c3b496; ndut_fmv=6b29a69122915448cefa4651753dae56362a00225dcfdf4a2144cf0e72d35ac5028b940438655979f423c8968886b5487b9e64d41d1c9f75bafbda6a81e4dc386dbcf7d1af60c920aa1833832d5d4eafa9e6824ea3b6a9cab0742900bae4c2d18f9ad65cb4b4e20a4eb186a6ee513295; ndut_fmt=9C04E47A8C33DCF3CF8052D90C04A5A265A37858BB642858306301BDF4D47DAE; g_state={"i_l":0,"i_ll":1767608852245,"i_b":"zbTh5ikhDjTPFpeWlEnCNuVIi6v1g2pvWSaVcBylKjc","i_e":{"enable_itp_optimization":1}}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send video/file directly, I'll upload to TeraBox.")

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get file (video or document)
    msg = update.message
    file = msg.video or msg.document
    if not file:
        await msg.reply_text("Send a file/video, not text.")
        return

    await msg.reply_text("Downloading file...")
    f = await file.get_file()
    file_name = file.file_path.split("/")[-1]
    save_path = "/tmp/" + file_name
    await f.download_to_drive(save_path)

    await msg.reply_text("Uploading to TeraBox...")
    with open(save_path, "rb") as v:
        content = v.read()

    # Reserve upload slot
    pre = requests.post(
        "https://www.terabox.com/api/precreate",
        data={"path": "/" + file_name, "size": len(content), "isdir": 0, "autoinit": 1, "block_list": "[]"},
        headers={"Cookie": TERABOX_COOKIE}
    )
    if not pre.ok or "uploadid" not in pre.text:
        await msg.reply_text("TeraBox rejected precreate. Cookie may be invalid.")
        return

    upload_id = pre.json().get("uploadid")

    # Upload actual file
    up = requests.post(
        "https://www.terabox.com/api/create",
        data={"path": "/" + file_name, "uploadid": upload_id},
        files={"file": (file_name, content)},
        headers={"Cookie": TERABOX_COOKIE}
    )
    if not up.ok:
        await msg.reply_text("Upload failed.")
        return

    tb_path = up.json().get("path")

    # Create share link
    share = requests.post(
        "https://www.terabox.com/share/set",
        data={"path_list": f"[\"{tb_path}\"]"},
        headers={"Cookie": TERABOX_COOKIE}
    )
    if not share.ok:
        await msg.reply_text("File uploaded but share link failed.")
        return

    link = share.json().get("shorturl")
    await msg.reply_text(f"Done! Link:\n{link}")
    os.remove(save_path)

# Run bot
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, upload))
app.run_polling()
