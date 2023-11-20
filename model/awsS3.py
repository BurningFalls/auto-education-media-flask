from app import app
import boto3
import os

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = "quiz-image-delivery"

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def create_upload_folder():
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])


def get_s3_url(image, filename):
    create_upload_folder()

    local_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    with open(local_path, "wb") as file:
        file.write(image)

    s3.upload_file(local_path, S3_BUCKET, filename)
    os.remove(local_path)

    s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{filename}"

    return s3_url
