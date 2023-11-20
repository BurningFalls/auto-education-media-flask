GPT_NAME = "gpt-4"
GPT_PROMPT = """Generate only one True/False quiz and its answer based on the following statement,
            separated by a newline.
            Use 50% probability for True and 50% probability for False.
            Question: 
            Answer:"""


async def generate_quiz(text, client):
    messages = [{"role": "system", "content": GPT_PROMPT},
                {"role": "user", "content": text}]

    response = await client.chat.completions.create(
        model=GPT_NAME,
        messages=messages
    )
    quiz = response.choices[0].message.content

    question, answer = quiz_to_qna(quiz)

    return question, answer


def quiz_to_qna(quiz):
    qna = quiz.split("\n")

    question = qna[0]
    if ':' in question:
        question = question.split(':')[1]
    question = question.strip()

    answer_string = qna[len(qna) - 1]
    if ':' in answer_string:
        answer_string = answer_string.split(':')[1]
    answer_string = answer_string.strip()
    answer = (answer_string == "True")

    return question, answer
