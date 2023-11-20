import uuid
import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from openai import OpenAI

import model.awsS3 as awsS3
import model.dalle as dalle
import model.gpt as gpt
import model.youtube as youtube

QUIZ_AMOUNT = 5
SENTENCE_AMOUNT = 100

app = Flask(__name__)
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.route('/quiz/<video_id>', methods=['POST'])
def make_quiz(video_id):
    youtube_info = youtube.fetch_youtube_info(video_id)

    try:
        quiz_list = generate_quiz_list(youtube_info['transcripts'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'quizs': quiz_list,
        'title': youtube_info['title'],
        'creator': youtube_info['creator'],
        'duration': youtube_info['duration'],
        'viewCount': youtube_info['viewCount'],
        'category': youtube_info['category'],
        # 'transcripts': youtube_info['transcripts']
    })


def generate_quiz_list(transcripts):
    if QUIZ_AMOUNT == 0:
        return None

    text_list = transcript_to_textlist(transcripts)

    quiz_list = []

    for quiz_id, text in enumerate(text_list):
        try:
            question, answer = gpt.generate_quiz(text, client)
        except Exception as e:
            question, answer = None, None

        try:
            image = dalle.generate_image(question, client)

            unique_id = str(uuid.uuid4())
            image_name = f"image_{unique_id}.png"
            s3_url = awsS3.get_s3_url(image, image_name)
        except Exception as e:
            s3_url = None

        quiz_list.append({
            'question': question,
            'answer': answer,
            's3Url': s3_url
        })

    return quiz_list


def transcript_to_textlist(transcripts):
    texts = [part['text'] for part in transcripts]

    text_list = []

    interval = max(1, len(texts) // QUIZ_AMOUNT)
    text_length = min(interval, SENTENCE_AMOUNT)

    for i in range(0, len(texts), interval):
        sub_text = " ".join(texts[i:min(i + text_length, len(texts))])
        text_list.append(sub_text)
        if len(text_list) >= QUIZ_AMOUNT:
            break

    while len(text_list) < QUIZ_AMOUNT:
        text_list.append("")

    return text_list


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
