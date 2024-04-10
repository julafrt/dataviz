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
    return spotify_filtered

def plot_ranking_and_platforms(spotify_filtered, top_range=(0, 25)):
    min_range, max_range = top_range
    top_n_songs = spotify_filtered.iloc[min_range:max_range]

    selection = alt.selection_multi(fields=['track_name'])
    selection2 = alt.selection_interval()

    chart = alt.Chart(top_n_songs).mark_bar().encode(
        x='streams:Q',
        y=alt.Y('track_name:N', sort='-x'),
        color=alt.condition(selection, alt.value('darkgreen'), alt.value('lightgray')),
        tooltip=[alt.Tooltip('track_name:N', title='Track Name'), alt.Tooltip('artist(s)_name:N', title='Artist(s) Name'), 'streams:Q', alt.Tooltip('in_spotify_playlists:Q', title='In Spotify Playlists')]
    ).properties(
        width=500,
        height=500,
        title=f'Top {max_range} Songs Streaming Ranking'
    ).add_selection(selection).transform_filter(selection2)

    platform = alt.Chart(top_n_songs).mark_bar().transform_fold(
        ['in_spotify_playlists', 'in_apple_playlists', 'in_deezer_playlists'],
        as_=['Metric', 'Value']
    ).encode(
        x=alt.X('sum(Value):Q', stack="normalize", axis=alt.Axis(format='%')),
        y=alt.Y(
            'track_name:N',
            title='Track Names',
            sort=alt.EncodingSortField(field='streams', order='descending')
        ),
        tooltip=[alt.Tooltip('track_name:N', title='Track Name'), alt.Tooltip('artist(s)_name:N', title='Artist(s) Name'), alt.Tooltip('in_spotify_playlists:Q', title='In Spotify Playlists'), alt.Tooltip('in_apple_playlists:Q', title='In Apple Playlists'), alt.Tooltip('in_deezer_playlists:Q', title='In Deezer Playlists')],
        color=alt.Color(
            'Metric:N',
            scale=alt.Scale(
                domain=['in_spotify_playlists', 'in_apple_playlists', 'in_deezer_playlists'],
                range=['darkgreen', 'crimson', 'MediumOrchid']
            ),
            title='Metrics'
        )
    ).properties(
        width=500,
        height=500,
        title='Importance of Platforms for Songs'
    ).transform_filter(selection2).add_selection(selection)    

    return chart, platform

def plot_analysis_and_metrics(spotify_filtered, x_axis='energy_%', y_axis='danceability_%'):
    scatter_base = alt.Chart(spotify_filtered).mark_circle().encode(
        x=alt.X(x_axis + ':Q', title=x_axis.replace('_', ' ').title()),
        y=alt.Y(y_axis + ':Q', title=y_axis.replace('_', ' ').title()),
        tooltip=[alt.Tooltip('track_name:N', title='Track Name'), alt.Tooltip('artist(s)_name:N', title='Artist(s) Name'), alt.Tooltip(x_axis + ':Q', title=x_axis.replace('_', ' ').title()), alt.Tooltip(y_axis + ':Q', title=y_axis.replace('_', ' ').title()), 'streams:Q']
    ).properties(
        width=500,
        height=500,
        title='Song Analysis'
    )

    dots = alt.Chart(spotify_filtered).transform_fold(
        ['danceability_%', 'valence_%', 'energy_%', 'acousticness_%', 'liveness_%', 'speechiness_%'],
        as_=['Metric', 'Value']
    ).mark_circle().encode(
        x=alt.X('Value:Q', title='Value'),
        y=alt.Y('Metric:N', title=None, sort='-x'),
        tooltip=[alt.Tooltip('track_name:N', title='Track Name'), alt.Tooltip('artist(s)_name:N', title='Artist(s) Name'), alt.Tooltip('Value:Q', title='Metric'), 'streams:Q']
    ).properties(
        width=500,
        height=250
    )

    return scatter_base, dots

def plot_mode_distribution_and_pie_chart(spotify_filtered):
    base = alt.Chart(spotify_filtered).transform_calculate(
        mode=alt.expr.if_(alt.datum.mode == 'Minor', 'Minor', 'Major')
    ).properties(
        width=300,
        height=300
    )

    left = base.transform_filter(
        alt.datum.mode == 'Minor'
    ).encode(
        y=alt.Y('key:N', axis=None),
        x=alt.X('count(key):N',
                title='Nb of Songs',
                sort=alt.SortOrder('descending')),
        color='count(mode):N',
        tooltip=['mode:N', 'key:N', 'count(mode):N']
    ).mark_bar().properties(title='Minor')

    middle = base.encode(
        y=alt.Y('key:N', axis=None),
        text=alt.Text('key:N'),
    ).mark_text().properties(width=40)

    right = base.transform_filter(
        alt.datum.mode == 'Major'
    ).encode(
        y=alt.Y('key:N', axis=None),
        x=alt.X('count(key):N', title='Nb of Songs'),
        color='count(mode):N',
        tooltip=['mode:N', 'key:N', 'count(mode):N']
    ).mark_bar().properties(title='Major')

    modes = alt.concat(left, middle, right, spacing=5)

    pie_chart = alt.Chart(spotify_filtered).mark_arc().encode(
        theta='count(mode):N',
        color=alt.Color('mode:N', scale=alt.Scale(domain=['Major', 'Minor'], range=['darkgreen', 'dimgray'])),
        tooltip=['mode:N', 'count(mode):N']
    ).properties(
        width=400,
        height=400,
        title='Mode Distribution'
    )

    return modes, pie_chart

# Main App
def main():
    st.set_page_config(
        page_title="Top 100 Spotify Music Analysis", page_icon="⬇", layout="centered"
    )
    st.title('Spotify Song Analysis Overview')

    # Data Acquisition
    spotify_filtered = get_data()

    # Interactive Controls
    songs_count_selector = st.slider('Top Songs', 0, 100, (0, 25), key='top_songs')
    x_axis = st.selectbox('X-Axis', ['danceability_%', 'valence_%', 'energy_%'], key='x_axis')
    y_axis = st.selectbox('Y-Axis', ['danceability_%', 'valence_%', 'energy_%'], key='y_axis')

    # Display Charts
    ranking_chart, platform_chart = plot_ranking_and_platforms(spotify_filtered, songs_count_selector)
    st.altair_chart(ranking_chart, use_container_width=True)
    st.altair_chart(platform_chart, use_container_width=True)

    analysis_chart, metrics_chart = plot_analysis_and_metrics(spotify_filtered, x_axis, y_axis)
    st.altair_chart(analysis_chart, use_container_width=True)
    st.altair_chart(metrics_chart, use_container_width=True)

    modes_chart, pie_chart = plot_mode_distribution_and_pie_chart(spotify_filtered)
    st.altair_chart(modes_chart, use_container_width=True)
    st.altair_chart(pie_chart, use_container_width=True)

if __name__ == "__main__":
    main()
