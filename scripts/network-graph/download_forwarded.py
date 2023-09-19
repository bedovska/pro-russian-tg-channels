
import re

import pandas as pd

from datetime import datetime
from pathlib import Path
from fire import Fire
from telethon import TelegramClient
from telethon.types import ChannelForbidden

import warnings
warnings.filterwarnings("ignore", category=FutureWarning) 


async def do_in_telegram(client: TelegramClient) -> None:
    # await client.send_message("obedovska", "воняеете")
    data_folder = Path("data")
    channels = pd.read_csv(data_folder / "forwarded_chose.csv")
    channels = channels[(channels["status"] == "good")]
    channel_names = channels["chan_name"].tolist()
    channel_names = channel_names[:50]
    
    for idx, channel_name in enumerate(channel_names):
        print(f"{idx+1}/{len(channel_names)}: {channel_name}")
        messages_df = pd.DataFrame()
        # msg_limit = 1000
        date_from = datetime(year=2023, month=1, day=1)
        # date_from = datetime(year=2023, month=4, day=15)

        async for msg in client.iter_messages(
            channel_name,
            reverse=True,
            offset_date=date_from,
        ):
        

            if msg.reactions is not None:
                reactions = {r.reaction.emoticon: r.count for r in msg.reactions.results}
            else:
                reactions = {}

            if msg.forward is not None:
                not_hidden = msg.forward.chat is not None
                not_forbidden = not_hidden and not isinstance(msg.forward.chat, ChannelForbidden)

                is_forwarded = True
                forward_from = f"https://t.me/{msg.forward.chat.username}" if not_hidden and not_forbidden else ""
            else:
                is_forwarded = False
                forward_from = ""

            
            msg_item = {
                "id": msg.id,
                "date": msg.date.isoformat(),
                "views": msg.views,
                "reactions": reactions,
                "has_photo": msg.photo is not None,
                "has_video": msg.video is not None,
                "text": msg.text,
                "cur_date": datetime.now().isoformat(),
                "is_forwarded": is_forwarded,
                "forward_from": forward_from,
            }
            messages_df = messages_df.append(msg_item, ignore_index=True)


        messages_df = messages_df.sort_values(by="date", ascending=False)
        channel_nick = channel_name.split("/")[-1]
        messages_df.to_csv(f"{channel_nick}.csv", index=False)        


def main():
    
    api_id = 
    api_hash = 
    print("there")

    with TelegramClient("creds/telegram/anon", api_id, api_hash) as client:
        client.loop.run_until_complete(do_in_telegram(client))


if __name__ == "__main__":
    Fire(main)
