import pickle
import streamlit as st
import requests
from joblib import load
import pandas as pd

def trigger_rerun():
    # Only used in the search form; not used in pagination anymore
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=1a106797f56f0a412936adce2da2a7df&language=en-US"
    response = requests.get(url)
    data = response.json()
    poster_path = data.get('poster_path')
    if poster_path:
        return "https://image.tmdb.org/t/p/w500/" + poster_path
    else:
        return "https://via.placeholder.com/500x750?text=No+Image"

def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), key=lambda x: x[1], reverse=True)
    rec_names = []
    rec_posters = []
    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        rec_names.append(movies.iloc[i[0]].title)
        rec_posters.append(fetch_poster(movie_id))
    return rec_names, rec_posters

def show_header():
    st.markdown("""
        <style>
        .stButton > button {
            width: 150px;
            white-space: normal;
        }
        </style>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("🏠 Home"):
            st.session_state.page = 'home'
            st.session_state.movie_page = 0
            st.session_state.selected_movie = None

    movie_list = movies['title'].values
    with st.form(key='movie_search_form', clear_on_submit=False):
        selected_movie = st.selectbox("Search for a Movie", movie_list, key='search_movie')
        submit_search = st.form_submit_button("Recommend Movie")
        if submit_search:
            st.session_state.selected_movie = selected_movie
            st.session_state.page = 'recommend'
            trigger_rerun()  # Use forced rerun only here if needed

def show_home():
    st.title("Home")
    st.markdown("Select a movie by clicking its button to view similar movies.")

    total_pages = (len(movies) - 1) // 30 + 1

    # Using a number input with a key so that its value is linked to session_state.
    current_page = st.session_state.get('movie_page', 0) + 1
    new_page = st.number_input(
        "Go to page number",
        min_value=1,
        max_value=total_pages,
        key="page_input",
        value=current_page,
        step=1
    )
    if new_page != current_page:
        st.session_state.movie_page = new_page - 1

    start_index = st.session_state.get('movie_page', 0) * 30
    end_index = start_index + 30
    current_movies = movies.iloc[start_index:end_index]

    num_columns = 5
    cols = st.columns(num_columns)
    for idx, row in current_movies.iterrows():
        col = cols[(idx - start_index) % num_columns]
        with col:
            poster_url = fetch_poster(row['movie_id'])
            st.image(poster_url, use_container_width=True)
            if st.button(row['title'], key=row['title']):
                st.session_state.selected_movie = row['title']
                st.session_state.page = 'recommend'
                # No forced rerun needed here

    col_prev, col_info, col_next = st.columns(3)
    with col_prev:
        if st.session_state.get('movie_page', 0) > 0:
            if st.button("⬅️ Previous Page"):
                st.session_state.movie_page -= 1
                # No forced rerun; button click already triggers a run
    with col_info:
        page_num = st.session_state.get('movie_page', 0) + 1
        st.markdown(f"**Page {page_num} of {total_pages}**")
    with col_next:
        if st.session_state.get('movie_page', 0) < total_pages - 1:
            if st.button("➡️ Next Page"):
                st.session_state.movie_page += 1
                # No forced rerun here either

def show_recommend():
    selected_movie = st.session_state.get('selected_movie', None)
    if not selected_movie:
        st.error("No movie selected.")
        return
    st.title(f"Movies similar to: {selected_movie}")
    rec_names, rec_posters = recommend(selected_movie)
    num_columns = 5
    cols = st.columns(num_columns)
    for i in range(len(rec_names)):
        col = cols[i % num_columns]
        with col:
            st.text(rec_names[i])
            st.image(rec_posters[i], use_container_width=True)
    if st.button("🔙 Go Back to Homepage"):
        st.session_state.page = 'home'
        st.session_state.movie_page = 0
        # No forced rerun here
movies = load('movie_list.joblib')
similarity = load('similarity.joblib')
#movies = load('movie_list.joblib')
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'movie_page' not in st.session_state:
    st.session_state.movie_page = 0
if 'selected_movie' not in st.session_state:
    st.session_state.selected_movie = None

show_header()

if st.session_state.page == 'home':
    show_home()
elif st.session_state.page == 'recommend':
    show_recommend()
