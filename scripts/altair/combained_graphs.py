import pandas as pd
from pathlib import Path
import altair as alt

data = pd.read_csv("data/stats/channel_info_full_with_lang.csv")
pd.DataFrame(data)

data['link'] = 'https://t.me/' + data['username']
data.loc[data['language_full'] == 'Macedonian', 'language_full'] = 'Serbian'
print(data.head)

data['creation_date_new'] = data['creation_date']
data.creation_date = data.creation_date.astype('datetime64[M]')
data = data.loc[data['language_full'].isin(["English", "Italian",])]


value_mapping = {'English': 'Англійська', 'Italian': 'Італійська'}
data['language_full'] = data['language_full'].map(value_mapping)

selection_multy = alt.selection_multi(on='mouseover')
selection_interval = alt.selection_interval(bind='scales')

# search_input = alt.selection_point(
#     fields=['Title'],
#     empty=False,  # Start with no points selected
#     bind=alt.binding(
#         input='search',
#         placeholder="Назва каналу",
#         name='Пошук ',

chart = alt.Chart(
	data,
	title=alt.Title(
	"Кількість підписників проросійських телеграм каналів",
	subtitle= ["Кожен кружечок є також гіперпосиланням на певний телеграм-канал"
			   # 'Кожен кружчок також є гіпер-посилання на канал, який у ньому закодований'
			   ],

	anchor='middle',
	orient='top',
	offset=20,
	)
	).encode(
    x=alt.X(
    	'creation_date:T',
    	scale=alt.Scale(zero=False),
    	axis = alt.Axis(minExtent = 30),
    	title = 'Дата створення',
    	timeUnit = 'yearmonthdate',
    	bin = False, 
    ).scale(
    	type = 'log',
    ),
    y=alt.Y(
    	"participants_count:Q",
    	bin = False, 
    	title = "Кількість підписників",
    	# axis=alt.Axis(minExtent=30),
    ).scale(
    	type="log",
    	base=2
    ),
    color = alt.condition(
		selection_multy, 
		alt.Color(
			field = 'language_full', 
			type = 'nominal',
			scale=alt.Scale(scheme='accent'),
			title = 'Мова каналу:',
		),
		alt.value('grey')
	),
	size = alt.Size(
		# 'count_language_per_date:Q',
		scale=alt.Scale(range=[1,10]),
		condition=[
			{"test": {"field": "language_full", "equal": "English"}, "value": 1000},
			{"test": {"field": "language_full", "equal": "Italian"}, "value": 700},
			# {"test": {"field": "language_full", "equal": "Serbian"}, "value": 500},
			# {"test": {"field": "language_full", "equal": "Turkish"}, "value": 400},
			# {"test": {"field": "language_full", "equal": "French"}, "value": 300},
		],
	),
	opacity=alt.condition(selection_multy, alt.value(0.6), alt.value(0.5)),
    tooltip=[
    	alt.Tooltip('title:N',title = 'Назва'),
    	alt.Tooltip('language_full:N', title = "Мова"),
    	alt.Tooltip('yearmonthdate(creation_date_new):T', title = 'Створення'),
    	# alt.Tooltip('verified:N', title = 'Верифікація'),
    	# alt.Tooltip('link', title = 'Link'),
    ],
    href = 'link:N',
).properties(
    width=1000,
    height=700,
).transform_filter(
	'year(datum.creation_date) > 2020'
).add_params(selection_multy, 
			selection_interval,
			# search_input,
).mark_circle(
	size = 700,
)

chart['usermeta'] = {
    "embedOptions": {
        'loader': {'target': '_blank'}
    }
}


chart.save('viz/altair-charts/dots_info.html')