import streamlit as st
import pandas as pd
import altair as alt

def get_data():
    url="https://tinyurl.com/y822sfzy"
    df = pd.read_csv("https://tinyurl.com/y822sfzy", encoding='latin-1')
    spotify_cleaned = df.dropna()
    spotify_filtered = spotify_cleaned.loc[spotify_cleaned['streams'].str.isnumeric(), :]
    spotify_filtered.loc[:, 'streams'] = spotify_filtered['streams'].astype(int)
    spotify_filtered.loc[:, 'in_deezer_playlists'] = spotify_filtered['in_deezer_playlists'].astype(str)
    spotify_filtered.loc[:, 'in_deezer_playlists'] = spotify_filtered['in_deezer_playlists'].str.replace(',', '').astype(int)
    spotify_filtered = spotify_filtered.sort_values('streams', ascending=False)
    spotify_filtered = spotify_filtered.head(100)
    spotify_filtered['track_name'] = spotify_filtered['track_name'].str.replace("ï¿½ï¿½o", "ñorita")
    spotify_filtered['artist(s)_name'] = spotify_filtered['artist(s)_name'].str.replace("ï¿½ï¿½ne", "aneskin")
    spotify_filtered['artist(s)_name'] = spotify_filtered['artist(s)_name'].str.replace("ï¿½ï¿½reo", "éreo")
    spotify_filtered['track_name'] = spotify_filtered['track_name'].str.replace("ï¿½", "ON")
    spotify_filtered['track_name'] = spotify_filtered['track_name'].str.replace("ï¿", "O")
    return spotify_filtered

# Chart Creation
def plot_top_songs(spotify_filtered, top_range=(0, 25), x_axis='energy_%', y_axis='danceability_%'):
    min_range, max_range = top_range
    range_val = max_range - min_range
    max_dim = range_val/6
    top_n_songs = spotify_filtered.iloc[min_range:max_range]

    selection = alt.selection_multi(fields=['track_name'])
    selection2 = alt.selection_interval()

    chart = alt.Chart(top_n_songs).mark_bar().encode(
        x=alt.X('streams:Q',title='Number of streams'),
        y=alt.Y('track_name:N', sort='-x', title='Track Names'),
        color=alt.condition(selection, alt.value('black'), alt.value('lightgray')),
        tooltip=[alt.Tooltip('track_name:N', title='Track Name'), alt.Tooltip('artist(s)_name:N', title='Artist(s) Name'), 'streams:Q', alt.Tooltip('in_spotify_playlists:Q', title='In Spotify Playlists')]
    ).properties(
        width=300,
        height=500,
        title=f'Top {max_range} Songs Streaming Ranking'
    ).add_selection(selection).transform_filter(selection2)

    scatter_base = alt.Chart(top_n_songs).mark_circle().encode(
        x=alt.X(x_axis + ':Q', title=x_axis.replace('_', ' ').title()),
        y=alt.Y(y_axis + ':Q', title=y_axis.replace('_', ' ').title()),
        color=alt.condition(selection, alt.value('darkgreen'), alt.value('lightgray')),
        tooltip=[alt.Tooltip('track_name:N', title='Track Name'), alt.Tooltip('artist(s)_name:N', title='Artist(s) Name'), alt.Tooltip(x_axis + ':Q', title=x_axis.replace('_', ' ').title()), alt.Tooltip(y_axis + ':Q', title=y_axis.replace('_', ' ').title()), 'streams:Q']
    ).properties(
        width=300,
        height=300,
        title='Song Analysis'
    ).add_selection(selection2)

    dots = alt.Chart(top_n_songs).transform_fold(
        ['danceability_%', 'valence_%', 'energy_%', 'acousticness_%', 'liveness_%', 'speechiness_%'],
        as_=['Metric', 'Value']
    ).mark_circle().encode(
        x=alt.X('Value:Q', title='Value'),
        y=alt.Y('Metric:N', title=None, sort='-x'),
        color=alt.condition(selection, alt.value('darkgreen'), alt.value('lightgray')),
        opacity=alt.condition(selection2, alt.value(1.0), alt.value(0.3)),
        tooltip=[alt.Tooltip('track_name:N', title='Track Name'), alt.Tooltip('artist(s)_name:N', title='Artist(s) Name'), alt.Tooltip('Value:Q', title='Metric'), 'streams:Q']
    ).properties(
        width=400,
        height=200
    )

    platform = alt.Chart(top_n_songs).mark_bar().transform_fold(
        ['in_spotify_playlists', 'in_apple_playlists', 'in_deezer_playlists'],
        as_=['Metric', 'Value']
    ).encode(
        x=alt.X('sum(Value):Q', stack="normalize", axis=alt.Axis(format='%'), title='Percentage of repartition'),
        y=alt.Y(
            'track_name:N',
            title='Track Names',
            sort=alt.EncodingSortField(field='streams', order='descending')
        ),
        tooltip=[alt.Tooltip('track_name:N', title='Track Name'), alt.Tooltip('artist(s)_name:N', title='Artist(s) Name'), alt.Tooltip('in_spotify_playlists:Q', title='In Spotify Playlists'), alt.Tooltip('in_apple_playlists:Q', title='In Apple Playlists'), alt.Tooltip('in_deezer_playlists:Q', title='In Deezer Playlists')],
        color=alt.condition(
            selection,
            alt.Color(
                'Metric:N',
                scale=alt.Scale(
                    domain=['in_spotify_playlists', 'in_apple_playlists', 'in_deezer_playlists'],
                    range=['darkgreen', 'crimson', 'MediumOrchid']
                ),
                title='Metrics', legend=alt.Legend(legendX=300)
            ), alt.value('lightgray')
        )
    ).properties(
        width=300,
        height=500,
        title='Importance of Platforms for Songs'
    ).transform_filter(selection2).add_selection(selection)    

    base = alt.Chart(top_n_songs).transform_calculate(
        mode=alt.expr.if_(alt.datum.mode == 'Minor', 'Minor', 'Major')
    ).properties(
        width=200,
        height=250
    )

    left = base.transform_filter(
        alt.datum.mode == 'Minor'
    ).encode(
        y=alt.Y('key:N', axis=None),
        x=alt.X('count(key):N',
                title='Nb of Songs',
                sort=alt.SortOrder('descending'), scale=alt.Scale(domain=[0, max_dim])),
        color=alt.Color('count(mode):N',legend=None),
        tooltip=['mode:N', 'key:N', 'count(mode):N']
    ).mark_bar().properties(title='Minor')

    middle = base.encode(
        y=alt.Y('key:N', axis=None),
        text=alt.Text('key:N'),
    ).mark_text().properties(width=15)

    right = base.transform_filter(
        alt.datum.mode == 'Major'
    ).encode(
        y=alt.Y('key:N', axis=None),
        x=alt.X('count(key):N', title='Nb of Songs', scale=alt.Scale(domain=[0, max_dim])),
        color='count(mode):N',
        tooltip=['mode:N', 'key:N', 'count(mode):N']
    ).mark_bar().properties(title='Major')

    modes = left| middle| right
    modes = modes.transform_filter(selection2).transform_filter(selection)

    pie_chart = alt.Chart(top_n_songs).mark_arc().encode(
        theta='count(mode):N',
        color=alt.Color('mode:N', scale=alt.Scale(domain=['Major', 'Minor'], range=['darkgreen', 'dimgray'])),
        tooltip=['mode:N', 'count(mode):N']
    ).properties(
        width=250,
        height=250,
        title='Mode Distribution'
    ).transform_filter(selection).transform_filter(selection2)

    return (chart | platform) & (modes | pie_chart) & (scatter_base | dots)

# Main App
def main():
    st.set_page_config(
        page_title="Top 100 Spotify Music Analysis", page_icon="🎵", layout="wide"
    )
    st.title('Top 100 Spotify Music Analysis')

    body = "Nowadays, music streaming has played a very important role in young people’s entertainment life. Along with the platforms, the music streaming market worldwide is projected to reach a revenue of US$29.60bn in 2024 with a revenue growth rate at 14.6%, according to Statista. Among the multitude of platforms available, Spotify stands out as one of the most popular music streaming services. Our website attempts to explore the essence of what makes songs famous to the top of Spotify's charts in 2023, comparing their popularity across various platforms. Through insightful visualizations, we aim to assist industry experts in crafting the next big hits for business growth, while also guiding music enthusiasts to discover songs with similar characteristics to their favorites. Join us in exploring the heartbeat of today's music scene !"

    st.markdown(body, unsafe_allow_html=False, *, help=None)

    # Data Acquisition
    spotify_filtered = get_data()

    # Interactive Controls
    songs_count_selector = st.slider('Top Songs', 0, 100, (0, 25), key='top_songs')

    col1, col2 = st.columns(2)

    with col1:
        x_axis = st.selectbox('X-Axis', ['danceability_%', 'valence_%', 'energy_%', 'acousticness_%', 'liveness_%', 'speechiness_%'], key='x_axis')
    
    with col2:
        y_axis = st.selectbox('Y-Axis', ['valence_%', 'energy_%', 'acousticness_%', 'liveness_%', 'speechiness_%','danceability_%'], key='y_axis')

    # Display Charts
    st.altair_chart(plot_top_songs(spotify_filtered, songs_count_selector, x_axis, y_axis), use_container_width=True)

if __name__ == "__main__":
    main()
