import uuid
import os
import asyncio

from dotenv import load_dotenv
from flask import Flask, jsonify
from openai import AsyncOpenAI

import model.awsS3 as awsS3
import model.dalle as dalle
import model.gpt as gpt
import model.youtube as youtube

QUIZ_AMOUNT = 5
SENTENCE_AMOUNT = 100

app = Flask(__name__)
load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.route('/quiz/<video_id>', methods=['POST'])
def make_quiz(video_id):
    youtube_info = youtube.fetch_youtube_info(video_id)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        quiz_list = loop.run_until_complete(generate_quiz_list(youtube_info['transcripts']))
        loop.close()
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


async def process_text(text):
    try:
        gpt_result = await gpt.generate_quiz(text, client)
        question, answer = gpt_result[0], gpt_result[1]
    except Exception as e:
        print("generate quiz error: ", e)
        question, answer = None, None

    try:
        image = await dalle.generate_image(question, client)

        unique_id = str(uuid.uuid4())
        image_name = f"image_{unique_id}.png"
        s3_url = awsS3.get_s3_url(image, image_name)
    except Exception as e:
        print("generate_image error: ", e)
        s3_url = None

    return {
        'question': question,
        'answer': answer,
        's3Url': s3_url
    }


async def generate_quiz_list(transcripts):
    if QUIZ_AMOUNT == 0:
        return None

    text_list = transcript_to_textlist(transcripts)

    tasks = []
    for text in text_list:
        tasks.append(process_text(text))

    quiz_list = await asyncio.gather(*tasks)

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
