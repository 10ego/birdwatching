from flask import Flask
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import utils
from html import unescape

twitter = utils.TwitterAPI()
server = Flask(__name__)
app = dash.Dash(
    __name__,
    external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'],
    server = server
    )

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Birdwatching</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css?family=Ledger&display=swap" rel="stylesheet">
    </head>
    <body>
    {%app_entry%}
    </body>
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>

</html>
"""

trends = twitter.get_trends()[0]

app.layout = html.Div([
    html.Span([
        html.Div(dcc.Input(id='query-box', type='text')),
        html.Button('listen', id='button'),
        html.Label(
            [
                "Search type:",
                dcc.Dropdown(
                    id = 'dropdown',
                    options=[
                        {'label': 'Mixed', 'value':'mixed'},
                        {'label': 'Popular', 'value':'popular'},
                        {'label': 'Recent', 'value': 'recent'}
                    ],
                    value='mixed',
                    style={'width':'160px'}
                )
            ]
        )
    ]),
    html.Div(
        id='trending',
        style={'padding-left':'15%', 'padding-right':'15%'},
        children=html.Div([
            html.H5("Trending hashtags in Canada as of " + trends['as_of']),
            html.I(str.join(", ", [trend['name'] for trend in trends['trends']]))
            ])
    ),
    html.Div(id='output', style={'padding':'15%'})
])


@app.callback(
    Output('output','children'),
    [Input('button','n_clicks'), Input('query-box', 'n_submit'), Input('dropdown','value')],
    [State('query-box', 'value')]
)
def update_output(n_clicks, n_submit, dropdown, value):
    if value is None or value == "":
        return html.Div()
    if n_clicks and value or n_submit and value:
        results = twitter.query_tweets(value, dropdown)
        results = results['statuses']
        hashtags = [result['entities']['hashtags'] for result in results] # Grab 'text' key for hashtag value
        tweet_texts = [result['full_text'] for result in results]
        sensitives=[]
        for result in results:
            try:
                sensitives.append(result['possibly_sensitive'])
            except:
                sensitives.append(False)
        #sensitive = [result['possibly_sensitive'] for result in results]

        user_names = [result['user']['name'] for result in results]
        user_descriptions = [result['user']['description'] for result in results]
        user_profiles = twitter.get_user([str(result['user']['id']) for result in results])
        RENDERED_OUTPUT = [html.Hr(style={'width':'75%'})]
        for hashtag, tweet_text, user_name, user_desc, user_profile, sensitive in zip(hashtags, tweet_texts, user_names, user_descriptions, user_profiles, sensitives):
            hashtag = ['#'+tag['text'] for tag in hashtag]
            if sensitive is True:
                tweet_text = "(POTENTIALLY SENSITIVE)\n" + tweet_text
            OUTPUT = html.Div([
                html.A(
                    "@{} ({})".format(user_profile, user_name),
                    href="https://twitter.com/"+user_profile,
                    target="_blank"
                    ),
                html.P("User Description: " + user_desc),
                html.B("Associated hashtags used:"),
                html.Br(),
                html.I(str.join(', ', hashtag)),
                html.Br(),
                html.B("Original tweet:"),
                html.Br(),
                html.P(unescape(tweet_text)),
                #html.P("Potentially sensitive: ", sensitive),
                html.Hr(style={'width':'75%'})
            ])
            RENDERED_OUTPUT.append(OUTPUT)

        return html.Div(RENDERED_OUTPUT)
    

if __name__ == '__main__':
    #app.run_server(debug=True, host='0.0.0.0')
    app.run_server()
