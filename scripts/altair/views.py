import pandas as pd
import altair as alt

from pathlib import Path
from tqdm.cli import tqdm

selection_multy = alt.selection_multi(on='mouseover')
selection_interval = alt.selection_interval(bind='scales')

viz_folder = Path("viz/altair-charts")

def plot_views_per_lang(messages_df):
	# langs = ["English", "Italian"]
	langs = ["Англійська", "Італійська"]
	messages_df = messages_df[messages_df["language"].isin(langs)]
	messages_df.date = messages_df.date.astype('datetime64[W]')
	# print(messages_df.head())


	chart = alt.Chart(
		messages_df,
		title=alt.Title(
		"Середня кількість переглядів телеграм-каналів за англійською й італійською мовами (січень–квітень 2023 року)",
		# subtitle="Середня кількість переглядів телеграм-каналів англійською та італійською мовами від січня до квітня 2023 року",
		anchor='middle',
		orient='top',
		offset=20
		)
		).encode(
		x=alt.X(
			"date:T",
			# scale=alt.Scale(zero=False),
    		# axis = alt.Axis(minExtent = 30),
    		title = 'Дата створення',
			),
		y=alt.Y(
			'count()',
			# scale=alt.Scale(zero=False),
			# axis = alt.Axis(minExtent = 30),
			title = 'Кількість переглядів'
			),
		color=alt.condition(
		selection_multy, 
		alt.Color(
			"language:N",
			title = 'Мова каналу:',
			scale=alt.Scale(scheme='tableau20'),
			),
			alt.value('grey')
		),
		opacity=alt.condition(selection_multy, alt.value(0.9), alt.value(0.5)),
    	tooltip = alt.Tooltip('language:N'),
	).properties(
	    width=1000, height=600
	).add_params(
		selection_multy, 
		selection_interval,
	).mark_line(
		strokeWidth = 7,
		interpolate='monotone',
	).interactive()

	chart.save(viz_folder / 'views-per-lang.html')

def plot_view_per_channel(messages_df):
	langs = langs = ["Англійська", "Італійська"]
	messages_df = messages_df[messages_df["language"].isin(langs)]

	mean_views = messages_df.groupby("username").mean("views").reset_index()
	top_channels_username = mean_views \
							.sort_values(by="views", ascending=False) \
							.iloc[:10]["username"] \
							.tolist()

	messages_df = messages_df[messages_df["username"].isin(top_channels_username)]
	print(messages_df.shape)

	messages_df.date = messages_df.date.astype('datetime64[W]')


	chart = alt.Chart(
			messages_df,
			title=alt.Title(
		"Топ-10 телеграм-каналів за охопленням",
		# subtitle="Динаміка перегляду публікацій на кожному з десяти найпопулярніших каналів за охопленням",
		anchor='middle',
		orient='top',
		offset=20
		)
		).encode(
		x=alt.X(
			"date:T",
			scale=alt.Scale(zero=False),
    		axis = alt.Axis(minExtent = 30),
    		title = 'День перегляду',
			),
		y=alt.Y(
			"sum(views)",
			title = 'Кількість переглядів'
			),
		color=alt.condition(
		selection_multy, 
		alt.Color(
			"username:N",
			title = 'Перелік каналів:',
			scale=alt.Scale(scheme='tableau20'),
			sort=alt.EncodingSortField('count', op='count', order='descending')
			),
			alt.value('grey')
        ),
		opacity=alt.condition(selection_multy, alt.value(0.8), alt.value(0.5)),
		tooltip=[
		alt.Tooltip('username:N',title = 'Назва'),
    	alt.Tooltip('language:N', title = "Мова"),
    	# alt.Tooltip('creation_date:T', title = 'Створення'),
    	# alt.Tooltip('verified:N', title = 'Verified'),
    	],
    	href = 'link:N',
    # href = 'link:N',
	).properties(
	    width=1000, height=600
	).mark_line(
		strokeWidth = 7,
		interpolate='monotone',
	).add_params(
		selection_multy, 
		selection_interval,
	)

	chart.save(viz_folder / 'views-per-channel.html')


channels_stats = pd.read_csv("data/stats/eng_ital_prorus_channels.csv")
# channels_stats['link'] = 'https://t.me/' + channels_stats['username']
channels_username = channels_stats["username"].unique()
# print(channels_stats.shape)
# exit(0)

messages_df = pd.DataFrame()
messages_folder = Path("data/messages/channels-downloaded-2023-05-02-12/")
channels_filenames = list(messages_folder.glob("*.csv"))

tmp_folder = Path("archive/tmp")
messages_fn  = tmp_folder / "messages.csv"


if messages_fn.exists():
	messages_df = pd.read_csv(messages_fn)
else:

	for channel_fn in tqdm(channels_filenames):
		channel_username = channel_fn.stem

		if channel_username not in channels_username:
			print(f"There is no such username in stats: {channel_username}")
			continue

		channel_stat = channels_stats[channels_stats["username"] == channel_username].iloc[0]
		channel_df = pd.read_csv(channel_fn, usecols=["date", "views"])
		channel_df["language"] = channel_stat["language_full"]
		channel_df["username"] = channel_username
		channel_df['link'] = 'https://t.me/' + channel_username
		messages_df = pd.concat([messages_df, channel_df])
	messages_df.to_csv(messages_fn, index=False)

value_mapping = {'English': 'Англійська', 'Italian': 'Італійська'}
messages_df['language'] = messages_df['language'].map(value_mapping)


print(messages_df.shape)

plot_views_per_lang(messages_df)
plot_view_per_channel(messages_df)



