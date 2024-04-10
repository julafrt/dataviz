import streamlit as st
import pandas as pd
import altair as alt

# Data Acquisition
@st.cache_data
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

# Chart Creation
def plot_top_songs(top_range=(0, 25), x_axis='energy_%', y_axis='danceability_%'):
    min_range, max_range = top_range
    range = max_range - min_range
    max_dim = range/6
    top_n_songs = spotify_filtered.iloc[min_range:max_range]

    selection = alt.selection_multi(fields=['track_name'])
    #selection = alt.selection_interval(encodings=['y'], fields=['track_name'])
    selection2 = alt.selection_interval()

    chart = alt.Chart(top_n_songs).mark_bar().encode(
        x='streams:Q',
        y=alt.Y('track_name:N', sort='-x'),
        color=alt.condition(selection, alt.value('darkgreen'), alt.value('lightgray')),
        tooltip=[alt.Tooltip('track_name:N', title='track_name'.replace('_', ' ').title()),alt.Tooltip('artist(s)_name:N', title='artist(s)_name'.replace('_', ' ').title()),'streams:Q',alt.Tooltip('in_spotify_playlists:Q', title='in_spotify_playlists'.replace('_', ' ').title())]
    ).properties(
        width=500,
        height=500,
        title=f'Top {max_range} Songs Streaming Ranking'
    ).add_selection(selection).transform_filter(selection2)

    scatter_base = alt.Chart(top_n_songs).mark_circle().encode(
        x=alt.X(x_axis + ':Q', title=x_axis.replace('_', ' ').title()),
        y=alt.Y(y_axis + ':Q', title=y_axis.replace('_', ' ').title()),
        color=alt.condition(selection, alt.value('darkgreen'), alt.value('lightgray')),
        tooltip=[alt.Tooltip('track_name:N', title='track_name'.replace('_', ' ').title()),alt.Tooltip('artist(s)_name:N', title='artist(s)_name'.replace('_', ' ').title()), alt.Tooltip(x_axis + ':Q', title=x_axis.replace('_', ' ').title()), alt.Tooltip(y_axis + ':Q', title=y_axis.replace('_', ' ').title()), 'streams:Q']
    ).properties(
        width=500,
        height=500,
        title='Song Analysis'
        ).add_selection(selection2)

    dots = alt.Chart(top_n_songs).transform_fold(
        ['danceability_%', 'valence_%', 'energy_%', 'acousticness_%', 'liveness_%', 'speechiness_%'],
        as_=['Metric', 'Value']
    ).mark_circle().encode(
        x=alt.X('Value:Q', title='Value'),
        y=alt.Y('Metric:N', title=None, sort='-x'),
        color=alt.condition(selection, alt.value('darkgreen'), alt.value('lightgray')),
        tooltip=[alt.Tooltip('track_name:N', title='track_name'.replace('_', ' ').title()),alt.Tooltip('artist(s)_name:N', title='artist(s)_name'.replace('_', ' ').title()),alt.Tooltip('Value:Q', title='Metric'.replace('_', ' ').title()), 'streams:Q']
    ).properties(
        width=500,
        height=250
    )

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
        tooltip=[alt.Tooltip('track_name:N', title='track_name'.replace('_', ' ').title()),alt.Tooltip('artist(s)_name:N', title='artist(s)_name'.replace('_', ' ').title()),alt.Tooltip('in_spotify_playlists:Q', title='in_spotify_playlists'.replace('_', ' ').title()),alt.Tooltip('in_apple_playlists:Q', title='in_apple_playlists'.replace('_', ' ').title()),alt.Tooltip('in_deezer_playlists:Q', title='in_deezer_playlists'.replace('_', ' ').title())],
        color=alt.condition(
        selection,
        alt.Color(
            'Metric:N',
            scale=alt.Scale(
                domain=['in_spotify_playlists', 'in_apple_playlists', 'in_deezer_playlists'],
                range=['darkgreen', 'crimson', 'MediumOrchid']
            ),
            title='Metrics'
        ), alt.value('lightgray')
    )
    ).properties(
        width=500,
        height=500,
        title='Importance of platforms for songs'
    ).transform_filter(selection2).add_selection(selection)    

    base = alt.Chart(top_n_songs).transform_calculate(
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
                title='Nb of songs',
                sort=alt.SortOrder('descending'), scale=alt.Scale(domain=[0, max_dim])),
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
        x=alt.X('count(key):N', title='Nb of songs', scale=alt.Scale(domain=[0, max_dim])),
        color='count(mode):N',
        tooltip=['mode:N', 'key:N', 'count(mode):N']
    ).mark_bar().properties(title='Major')

    modes = alt.concat(left, middle, right, spacing=5).transform_filter(selection2).transform_filter(selection)

    pie_chart = alt.Chart(top_n_songs).mark_arc().encode(
        theta='count(mode):N',
        color=alt.Color('mode:N', scale=alt.Scale(domain=['Major', 'Minor'], range=['darkgreen', 'dimgray'])),
        tooltip=['mode:N', 'count(mode):N']
    ).properties(
        width=400,
        height=400,
        title='Mode Distribution'
    ).transform_filter(selection).transform_filter(selection2)
  return chart | platform | modes | pie_chart | scatter_base | dots

# Main App
def main():
  st.set_page_config(
      page_title="Top 100 Spotify Musics Analysis", page_icon="⬇", layout="centered"
  )
  st.title('Spotify Song Analysis Overview')

  # Data Acquisition
  spotify_filtered = get_data()

  # Interactive Controls
  songs_count_selector = st.slider('Top Songs', 0, 100, (0, 25), key='top_songs')
  x_axis = st.selectbox('X-Axis', ['danceability_%', 'valence_%', ...], key='x_axis')
  y_axis = st.selectbox('Y-Axis', ['danceability_%', 'valence_%', ...], key='y_axis')

  # Display Charts
  st.altair_chart(plot_top_songs(songs_count_selector, x_axis, y_axis), use_container_width=True)
  # You can add more charts here using st.altair_chart

if __name__ == "__main__":
  main()