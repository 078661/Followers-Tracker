
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import matplotlib.pyplot as plt
import os

# --- CONFIG ---
st.set_page_config("Real-time MoS Social Media Tracker", layout="wide")
TWITTER_BEARER_TOKEN = st.secrets["TWITTER_BEARER_TOKEN"]

# --- LOAD MINISTER DATA ---
df_ministers = pd.read_excel("Mos List.xlsx")
df_ministers.columns = [col.strip() for col in df_ministers.columns]

# --- HELPER FUNCTIONS ---
def get_twitter_followers(handle):
    try:
        url = f"https://api.twitter.com/2/users/by/username/{handle}?user.fields=public_metrics"
        headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
        response = requests.get(url, headers=headers)
        data = response.json()
        return data["data"]["public_metrics"]["followers_count"]
    except Exception as e:
        return None

def get_instagram_followers(handle):
    try:
        url = f"https://www.instagram.com/{handle}/"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        meta = soup.find("meta", property="og:description")
        content = meta["content"]
        followers_text = content.split(" Followers")[0]
        followers = followers_text.split(" ")[-1].replace(',', '')
        return int(float(followers.replace('k','000').replace('m','000000')))
    except:
        return None

# --- LOAD OR CREATE HISTORICAL DATA ---
today = datetime.date.today().strftime("%Y-%m-%d")
data_file = "data.csv"
if os.path.exists(data_file):
    df_history = pd.read_csv(data_file)
else:
    df_history = pd.DataFrame(columns=["Date", "Name", "Twitter Followers", "Instagram Followers"])

# --- REAL-TIME TRACKING ---
st.title("📊 MoS Social Media Tracker (X & Instagram)")
st.markdown("Auto-refreshes every 5 minutes • Historical trend chart below")

new_rows = []
real_time_data = []

with st.spinner("Fetching latest follower counts..."):
    for _, row in df_ministers.iterrows():
        name = row['Name'].strip()
        tw_handle = str(row['X Handle']).strip()
        insta_handle = str(row['Insta Handle']).strip()
        twitter_followers = get_twitter_followers(tw_handle)
        instagram_followers = get_instagram_followers(insta_handle)
        real_time_data.append([name, tw_handle, twitter_followers, insta_handle, instagram_followers])
        new_rows.append({
            "Date": today,
            "Name": name,
            "Twitter Followers": twitter_followers,
            "Instagram Followers": instagram_followers
        })

# --- SAVE TODAY'S DATA IF NEW ---
df_today = pd.DataFrame(new_rows)
if not ((df_history["Date"] == today).any()):
    df_history = pd.concat([df_history, df_today], ignore_index=True)
    df_history.to_csv(data_file, index=False)

# --- DISPLAY TABLE ---
st.subheader("📋 Current Follower Counts")
st.dataframe(pd.DataFrame(real_time_data, columns=["Name", "X Handle", "X Followers", "Instagram Handle", "Instagram Followers"]), use_container_width=True)

# --- PLOT GROWTH CHARTS ---
st.subheader("📈 Follower Growth Over Time")

fig, ax = plt.subplots(figsize=(12, 6))
for name in df_history["Name"].unique():
    user_data = df_history[df_history["Name"] == name].sort_values("Date")
    ax.plot(user_data["Date"], user_data["Twitter Followers"], label=f"{name} (X)")
ax.set_title("Twitter (X) Followers Growth")
ax.set_xlabel("Date")
ax.set_ylabel("Followers")
ax.legend(fontsize=8, loc='upper left')
plt.xticks(rotation=45)
st.pyplot(fig)

fig2, ax2 = plt.subplots(figsize=(12, 6))
for name in df_history["Name"].unique():
    user_data = df_history[df_history["Name"] == name].sort_values("Date")
    ax2.plot(user_data["Date"], user_data["Instagram Followers"], label=f"{name} (IG)")
ax2.set_title("Instagram Followers Growth")
ax2.set_xlabel("Date")
ax2.set_ylabel("Followers")
ax2.legend(fontsize=8, loc='upper left')
plt.xticks(rotation=45)
st.pyplot(fig2)

# --- DOWNLOAD OPTION ---
st.download_button("📥 Download Historical Data", df_history.to_csv(index=False), file_name="followers_history.csv", mime="text/csv")
st.caption("Built for PMO MoS real-time tracking. Twitter data via official API. Instagram via public data.")
