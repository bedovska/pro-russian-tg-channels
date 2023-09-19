import pandas as pd
from pathlib import Path
import altair as alt

data = pd.read_csv("data/stats/channel_info_full_with_lang.csv")
pd.DataFrame(data)

data['link'] = 'https://t.me/' + data['username']
data.loc[data['language_full'] == 'Macedonian', 'language_full'] = 'Serbian'
print(data.head)

data.creation_date = data.creation_date.astype('datetime64[M]')
data = data.loc[data['language_full'].isin(["English", "Italian"])]

value_mapping = {'English': 'Англійська', 'Italian': 'Італійська'}
data['language_full'] = data['language_full'].map(value_mapping)


# data.creation_date = data.creation_date.astype('datetime64[M]')
# data = data.loc[data['language_full'].isin(["English", "Russian", "Italian", "Serbian"])]

# select_year = alt.selection_single(
#     name='select', fields=['year'], init={'year': 2018},
#     bind=alt.binding_range(min=2018, max=2023, step=1))


# chart = alt.Chart(data).mark_point().encode(
# 	x = alt.X(field = 'creation_date', type = 'temporal', timeUnit = 'yearmonthdate'),
# 	y = alt.Y("count()"),
# 	color = alt.Color(field = 'language_full', type = 'nominal'),
# 	tooltip = alt.Tooltip('language_full'),
# 	order = alt.Order('creation_date:Q', sort='descending')
# 	).properties(width = 800, height = 600).resolve_scale(y = 'independent')

selection = alt.selection_point();


chart = alt.Chart(
	data, 
	title=alt.Title(
	"Динаміка створення телеграм-каналів",
	offset=20,
	)
	).encode(
	x = alt.X(
		field = 'creation_date', 
		type = 'temporal', 
		timeUnit = 'yearmonthdate',
		scale = alt.Scale(type='log'),
		# scale= alt.Scale(domain=(5, 20), clamp=True),
		title = 'Дата створення'
	),
	y = alt.Y(
		"count()",
		title = "Кількість каналів"

		),
	color = alt.condition(
				selection, 
		alt.Color(
		field = 'language_full', 
		type = 'nominal',
		scale=alt.Scale(scheme='tableau20'),
		title = "Мова каналів:",
		),
		# ).legend(None),
		alt.value('grey')
	),
	# column = 'language_full',
	opacity=alt.condition(selection, alt.value(0.8), alt.value(0.1)),
	tooltip = alt.Tooltip('language_full:N')
# ).transform_filter(
# 	'year(datum.creation_date) > 202' #сортую показувати динаміку створення від 2020р.
).resolve_scale(
	y = 'independent'
).properties(
    width=1000, height=600
).add_params(
	selection
).mark_line(
	# point=True,
	strokeWidth = 5,
	interpolate='monotone',
).interactive()

chart.save('viz/altair-charts/creation_time.html')




