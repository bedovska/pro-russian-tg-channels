
import pandas as pd
from pathlib import Path
import altair as alt

data = pd.read_csv("data/stats/channel_info_full_with_lang.csv")
pd.DataFrame(data)

# data.loc[data['language_full'] == 'Macedonian', 'language_full'] = 'Serbian'

data.creation_date = data.creation_date.astype('datetime64[M]')
data = data.loc[data['language_full'].isin(["English", "Italian"])]

value_mapping = {'English': 'Англійська', 'Italian': 'Італійська'}
data['language_full'] = data['language_full'].map(value_mapping)


selection = alt.selection_point();

# search_input = alt.selection_point(
#     fields=['Name'],
#     empty=False,  # Start with no points selected
#     bind=alt.binding(
#         input='search',
#         placeholder="Car model",
#         name='Search ',
#     )

participant_on_lang = alt.Chart(
	data,
	title=alt.Title(
	"Кількість знайдених Телеграм-каналів",
	offset=20,
	)
	).mark_bar(
	# interpolate='monotone',
    stroke='grey',
    # width = 50,
    align = 'center'
).encode(
	x = alt.X('language_full:N',
		sort='-y',
		title = "Мова каналу:",
		axis=alt.Axis(labelAngle= 360)
	),
	y = alt.Y(
		'count():Q',
		title = "Кількість каналів:"
		),
	# y2 = alt.Y2('mean(participants_count):Q',
	# 	title = 'mean of participants'),
	color = alt.condition(
		selection,
		alt.Color(
		field = 'language_full', 
		type = 'nominal',
		scale=alt.Scale(scheme='tableau20'),
		title = "Мова:"
		),
		alt.value('lightgrey')
	# ),
	# tooltip = alt.Tooltip('language_full:N'
	),
	tooltip = alt.Tooltip('count():Q', title = 'Кількість')
).add_params(selection
).properties(width = 500, height = 600)
# alt.layer(chart, participant_on_lang)

participant_on_lang.save('viz/altair-charts/amount_of_tg_channels.html')