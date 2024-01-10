import spotipy 
import time 
from spotipy.oauth2 import SpotifyOAuth

from flask import Flask, request, url_for, session, redirect

# initialize flask application
app = Flask(__name__)

#need to store token in session
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'aldkjfh2094857;.,$%^&'
TOKEN_INFO = 'token_info' #stores the token information

#routes
@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url() #getting the value of the url that we're going to transfer the user to
    return redirect(auth_url) #actually redirecting user to the url

@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    #exchange auth code for an access token 
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info #store token in session
    return redirect(url_for('save_discover_weekly', _external = True))

# route to save the Discover Weekly songs to a playlist
@app.route('/saveDiscoverWeekly')
def save_discover_weekly():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect('/')

    #success
    sp = spotipy.Spotify(auth=token_info['access_token'])

    discover_weekly_playlist_id = None
    saved_weekly_playlist_id = None
    current_playlists = sp.current_user_playlists()['items']

    for playlist in current_playlists: #loop through playlists to find targeted playlists
        if(playlist['name'] == "Discover Weekly"):
            discover_weekly_playlist_id = playlist['id']
        if(playlist['name'] == 'Saved Weekly'):
            saved_weekly_playlist_id = playlist['id']
        print(playlist['name'])
    
    if not discover_weekly_playlist_id:
        return "Discover Weekly not found, please add to library"
    
    #if saved weekly playlist doesn't already exist - create one
    if not saved_weekly_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Saved Weekly', True)
        saved_weekly_playlist_id = new_playlist['id']
    
    #get discover weekly tracks
    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist['items']: #get song uris and add to list
        song_uri = song['track']['uri']
        song_uris.append(song_uri)
    user_id = sp.current_user()['id']
    sp.user_playlist_add_tracks(user_id, saved_weekly_playlist_id, song_uris, None)

    # return a success message
    return ('Discover Weekly songs added successfully')



def get_token():
    token_info = session.get(TOKEN_INFO, None)
    #if token does not exist or is expired 
    if not token_info:
        redirect(url_for('login', _external=False))

    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    
    return token_info


#function to create spotify oauth
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = "bf23367820504c08a8e73816383f4be3",
        client_secret = "82b87fc221ef4faa8c882f741378ef1d",
        redirect_uri = url_for('redirect_page', _external=True,),
        scope = 'user-library-read playlist-modify-public playlist-modify-private'
    )

app.run(debug=True)

