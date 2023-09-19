
import re
import asyncio

import pandas as pd

from datetime import datetime
from typing import (List, Optional)
from pathlib import Path
from fire import Fire
from contextlib import suppress
from telethon import TelegramClient
from telethon.types import ChannelForbidden
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError
from telethon.errors.rpcerrorlist import ChannelPrivateError, ChannelInvalidError

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


async def check_channel_exists(channel_username):
    try:
        channel = await client.get_entity(channel_username)
        return True
    except ChannelPrivateError:
        return False
    except ChannelInvalidError:
        return False

    except ValueError:
        return False


async def download_messages(
    channel_name: str,
    date_from: datetime,
) -> Optional[pd.DataFrame]:
    messages = pd.DataFrame()

    channel_exists = await check_channel_exists(channel_name)


    try:
        async for msg in client.iter_messages(
            channel_name,
            reverse=True,
            offset_date=date_from,
            wait_time=30,
        ):


            if msg.forward is not None:
                not_hidden = msg.forward.chat is not None
                not_forbidden = not_hidden and not isinstance(msg.forward.chat, ChannelForbidden)

                is_forwarded = True
                forward_from = f"https://t.me/{msg.forward.chat.username}" \
                               if not_hidden and not_forbidden else ""
            else:
                is_forwarded = False
                forward_from = ""

            msg_item = {
                "id": msg.id,
                "date": msg.date.isoformat(),
                # "views": msg.views,
                # "reactions": reactions,
                # "has_photo": msg.photo is not None,
                # "has_video": msg.video is not None,
                # "text": msg.text,
                "cur_date": datetime.now().isoformat(),
                "is_forwarded": is_forwarded,
                "forward_from": forward_from,
            }
            messages = messages.append(msg_item, ignore_index=True)
        messages =  messages.sort_values(by="date", ascending=False)
    except ValueError:
        print(f"Error during message download: {channel_name}")
        return None
    except Exception:
        print(f"Error during message download: {channel_name}")
        return None

    return messages


def get_forwards(messages: pd.DataFrame, min_forwards: int) -> List[str]:
    forwards_with_count = messages["forward_from"].value_counts()
    forwards = forwards_with_count.index[forwards_with_count.values >= min_forwards].tolist()
    return forwards


async def download_channels(
    # client: TelegramClient,
    done_channels: List[str],
    waitlist_channels: List[str],
    out_folder: Path,
    min_forwards: int,
    max_round: int,
) -> None:
    await client.connect()

    done = [{ "name": ch, "round": 0 } for ch in done_channels]
    waitlist = [{ "name": ch, "round": 1 } for ch in waitlist_channels]
    date_from = datetime(year=2023, month=1, day=1)

    while waitlist:
        channel = waitlist.pop(0)
        done.append(channel)

        channel_name = channel["name"]
        channel_round = channel["round"]

        print(f"Current channel: {channel_name}, round: {channel_round}")
        print(f"Done: {len(done)}, waitlist: {len(waitlist)}")

        messages = await download_messages(channel_name, date_from)
        # messages = await download_messages(client, channel_name, date_from)
        if messages is None:
            continue

        if channel_round + 1 <= max_round:
            forwards = get_forwards(messages, min_forwards)
            waitlist_names = [ch["name"] for ch in waitlist]
            done_names = [ch["name"] for ch in done]
            forwards = [f for f in forwards \
                        if (f not in waitlist_names) and (f not in done_names)]
            waitlist += [{ "name": f , "round": channel_round + 1 } for f in forwards]
            print(f"Add {len(forwards)} channels into waitlist")
        print(f"Num of messages in channel: {len(messages)}")
        print()

        channel_short_name = channel_name.split("/")[-1]
        messages.to_csv(out_folder / f"{channel_short_name}.csv", index=False)



def load_done(folder: Path) -> List[str]:
    short_names = [fn.stem for fn in folder.glob("*.csv")]
    done = [f"https://t.me/{sn}" for sn in short_names]
    return done


def load_waitlist(folder: Path, min_forwards: int) -> List[str]:
    waitlist = []
    for fn in folder.glob("*.csv"):
        forwards = get_forwards(pd.read_csv(fn), min_forwards)
        forwards = [f for f in forwards if f not in waitlist]
        waitlist += forwards
    return waitlist


api_id = 
api_hash = 
client = TelegramClient("", api_id, api_hash)


def main():
    min_forwards = 10
    max_round = 20

    download_folder = Path("data/channels-downloaded")
    done_channels = load_done(download_folder) 
    waitlist_channels = load_waitlist(download_folder, min_forwards)
    waitlist_channels = [ch for ch in waitlist_channels if ch not in done_channels]

    # waitlist_channels = [ch for ch in waitlist_channels if "None" in ch]
    waitlist_channels = [ch for ch in waitlist_channels if "None" not in ch]
    print(f"Num of channels done: {len(done_channels)}")
    print(f"Num of channels in initial waitlist: {len(waitlist_channels)}")
    print()

    
    client.loop.run_until_complete(download_channels(
        # client,
        done_channels,
        waitlist_channels,
        download_folder,
        min_forwards,
        max_round,
    ))


if __name__ == "__main__":
    # Fire(main_v2)
    Fire(main)
