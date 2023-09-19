
"""
- creation date (channel_entity -> date)
- participants count (participants_count)
- telegram channel id (id)
- official channels (with star) (verified)
- language
- county
- about description (about)
"""
import asyncio

import pandas as pd

from typing import List
from telethon import TelegramClient
from telethon import functions

from pathlib import Path
from tqdm.cli import tqdm

import warnings
warnings.filterwarnings("ignore", category=FutureWarning) 


api_id = 
api_hash = 

client =  TelegramClient()

def load_done(folder: Path) -> List[str]:
    short_names = [fn.stem for fn in folder.glob("*.csv")]
    done = [f"https://t.me/{sn}" for sn in short_names]
    return done


def get_forwards(messages: pd.DataFrame, min_forwards: int) -> List[str]:
    forwards_with_count = messages["forward_from"].value_counts()
    forwards = forwards_with_count.index[forwards_with_count.values >= min_forwards].tolist()
    return forwards


def load_waitlist(folder, min_forwards):
    waitlist = []
    for fn in folder.glob("*.csv"):
        forwards = get_forwards(pd.read_csv(fn), min_forwards)
        forwards = [f for f in forwards if f not in waitlist]
        waitlist += forwards
    return waitlist


def print_object_attrs(obj):
    for field in [f for f in dir(obj) if "__" not in f]:
        print(f"{field}: {getattr(obj, field)}")


async def download_channel_info(channels: List[str]) -> pd.DataFrame:
    output_folder = Path("data/stats")
    tmp_stats_filename = output_folder / "channel_info_new_tmp.csv"
    full_stats_filename = output_folder / "channel_info_new_full.csv"

    if tmp_stats_filename.exists():
        file = pd.read_csv(tmp_stats_filename)
        stats_done = file["name"].tolist()

        channels = [ch for ch in channels if ch not in stats_done]
        channel_info = file.copy()
    else:
        channel_info = pd.DataFrame()

    await client.start()
    for channel in tqdm(channels):
        try:
            channel_entity = await client.get_entity(channel)
            result = await client(functions.channels.GetFullChannelRequest(channel_entity))
            await asyncio.sleep(3)

            channel_info_item = {
                "name": channel,
                "title": channel_entity.title,
                "about": result.full_chat.about,
                "id": result.full_chat.id,
                "creation_date": channel_entity.date.isoformat(),
                "verified": channel_entity.verified,
                "participants_count": result.full_chat.participants_count,
            }
            channel_info = channel_info.append(channel_info_item, ignore_index=True)

        except ValueError:
            print(f"Value error, channel: {channel}")
        channel_info.to_csv(tmp_stats_filename, index=False)
    channel_info.to_csv(full_stats_filename, index=False)


def main():
    download_folder = Path("data/messages/channels-downloaded-2023-05-02-12")
    channels_done = load_done(download_folder)
    channels_waitlist = load_waitlist(download_folder, 1)
    channels = list(set(channels_done) | set(channels_waitlist))

    client.loop.run_until_complete(download_channel_info(channels_done))

if __name__ == "__main__":
    main()

