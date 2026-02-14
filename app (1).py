import streamlit as st
import yt_dlp
import os
import zipfile
import smtplib
import re
import subprocess
from email.message import EmailMessage

st.set_page_config(
    page_title="Mashup Magic",
    page_icon="🎵",
    layout="wide"
)

SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", "")
EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD", "")

st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at top left, #121212, #1db95422), #121212;
    }
    
    .main-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 30px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }

    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        background: -webkit-linear-gradient(#eee, #333);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }

    .stButton>button {
        width: 100%;
        border-radius: 50px;
        height: 3em;
        background-color: #1DB954;
        color: white;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton>button:hover {
        background-color: #1ed760;
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(29, 185, 84, 0.3);
    }

    .stTextInput input, .stNumberInput input {
        background-color: #181818 !important;
        color: white !important;
        border: 1px solid #333 !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3844/3844724.png", width=80)
    st.title("How it works")
    st.info("""
    1. Enter a **Singer's Name**.
    2. Choose how many songs to sample.
    3. Set duration for each clip.
    4. We mix it and email you the ZIP!
    """)
    st.divider()
    st.caption("Powered by yt-dlp & FFmpeg")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("<h1>Mashup Magic 🎧</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #b3b3b3;'>Curate custom medleys from YouTube in seconds.</p>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        
        i1, i2 = st.columns(2)
        with i1:
            singer = st.text_input("🎤 Artist/Singer", placeholder="e.g. Ed Sheeran")
        with i2:
            email = st.text_input("📧 Delivery Email", placeholder="your@email.com")
            
        i3, i4 = st.columns(2)
        with i3:
            num_videos = st.number_input("🔢 Clips Count", min_value=11, value=15, step=1)
        with i4:
            duration = st.number_input("⏱ Clip Length (s)", min_value=21, value=30, step=1)
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        generate = st.button("Create My Mashup")

def is_valid_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)

def download_videos(singer, num_videos):
    os.makedirs("downloads", exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'noplaylist': True
    }
    search_query = f"ytsearch{num_videos}:{singer} songs"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([search_query])

def create_mashup(duration, output_file):
    trimmed_files = []
    for file in os.listdir("downloads"):
        input_path = os.path.join("downloads", file)
        trimmed_path = f"downloads/trimmed_{file}.mp3"
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path, "-t", str(duration),
            "-acodec", "mp3", trimmed_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        trimmed_files.append(trimmed_path)

    with open("file_list.txt", "w") as f:
        for file in trimmed_files:
            f.write(f"file '{file}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "file_list.txt", "-c", "copy", output_file
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def send_email(receiver, filename):
    msg = EmailMessage()
    msg["Subject"] = "🎵 Your Custom Mashup is Ready!"
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver
    msg.set_content(f"Hey! Your custom {singer} mashup is attached. Enjoy your listening session! 🎧")
    with open(filename, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="zip", filename=filename)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_PASSWORD)
        smtp.send_message(msg)

def cleanup():
    if os.path.exists("downloads"):
        for file in os.listdir("downloads"):
            os.remove(os.path.join("downloads", file))
        os.rmdir("downloads")
    for file in ["mashup.mp3", "mashup.zip", "file_list.txt"]:
        if os.path.exists(file):
            os.remove(file)

if generate:
    if not singer or not email:
        st.warning("Please provide both an artist and an email address.")
    elif not is_valid_email(email):
        st.error("That email format doesn't look right.")
    else:
        try:
            progress_bar = st.progress(0)
            with st.status("🪄 Casting Spells...", expanded=True) as status:
                st.write("🔍 Searching for tracks...")
                download_videos(singer, num_videos)
                progress_bar.progress(40)
                st.write("✂️ Trimming and blending...")
                create_mashup(duration, "mashup.mp3")
                progress_bar.progress(70)
                with zipfile.ZipFile("mashup.zip", 'w') as zipf:
                    zipf.write("mashup.mp3")
                st.write("📧 Sending to your inbox...")
                send_email(email, "mashup.zip")
                progress_bar.progress(100)
                status.update(label="Mashup Complete!", state="complete", expanded=False)
            st.balloons()
            st.success(f"Success! Check **{email}** for your zip file.")
            cleanup()
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            cleanup()
