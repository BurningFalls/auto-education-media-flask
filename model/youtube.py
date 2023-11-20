import os
import re
import requests
from youtube_transcript_api import YouTubeTranscriptApi


def fetch_youtube_info(video_id):
    google_api_key = os.getenv('GOOGLE_API_KEY')
    video_data, transcript_list = fetch_video_data(video_id, google_api_key)

    title = video_data['snippet']['title']
    creator = video_data['snippet']['channelTitle']
    video_duration = parse_duration(video_data['contentDetails']['duration'])
    youtube_views = video_data['statistics']['viewCount']
    category_id = video_data['snippet']['categoryId']

    transcript_data = fetch_transcript_data(transcript_list)

    return {
        'title': title,
        'creator': creator,
        'duration': video_duration,
        'viewCount': youtube_views,
        'category': category_id,
        'transcripts': transcript_data
    }


def fetch_video_data(video_id, google_api_key):
    url = (f'https://www.googleapis.com/youtube/v3/videos?'
           f'id={video_id}&key={google_api_key}&part=snippet,contentDetails,statistics,status')
    response = requests.get(url)
    video_data = response.json()
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    return video_data['items'][0], transcript_list


def fetch_transcript_data(transcript_list):
    transcript = transcript_list.find_transcript(['en'])
    transcript_parts = transcript.fetch()

    transcript_data = []

    for i in range(len(transcript_parts)):
        part = transcript_parts[i]
        text = part['text']
        start = part['start']

        if i == len(transcript_parts) - 1:
            duration = part['duration']
        else:
            next_start = transcript_parts[i + 1]['start']
            duration = next_start - start

        transcript_data.append({
            'text': text,
            'start': start,
            'duration': duration
        })

    return transcript_data


def parse_duration(duration):
    match = re.match(r'PT(\d+H)?(\d+M)?(\d+S)?', duration)
    hours = int(match.group(1)[:-1]) if match.group(1) else 0
    minutes = int(match.group(2)[:-1]) if match.group(2) else 0
    seconds = int(match.group(3)[:-1]) if match.group(3) else 0
    return hours * 3600 + minutes * 60 + seconds
