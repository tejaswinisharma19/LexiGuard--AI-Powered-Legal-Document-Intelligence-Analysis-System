import os

from aws.s3_service import S3Service


S3_OBJECT_KEY = "documents/legal_agreement.pdf"
DOWNLOAD_PATH = "test_documents/downloaded_legal_agreement.pdf"


s3_service = S3Service()

result = s3_service.download_file(
    S3_OBJECT_KEY,
    DOWNLOAD_PATH
)

print("Download successful!")
print(f"Downloaded file: {result}")
print(f"File exists locally: {os.path.exists(DOWNLOAD_PATH)}")

if os.path.exists(DOWNLOAD_PATH):
    file_size = os.path.getsize(DOWNLOAD_PATH)
    print(f"Downloaded file size: {file_size} bytes")