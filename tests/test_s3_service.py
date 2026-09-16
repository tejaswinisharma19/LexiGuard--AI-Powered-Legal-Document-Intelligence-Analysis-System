from aws.s3_service import S3Service


PDF_PATH = "test_documents/legal_agreement.pdf"
S3_OBJECT_KEY = "documents/test_legal_agreement.pdf"


s3_service = S3Service()

result = s3_service.upload_file(
    PDF_PATH,
    S3_OBJECT_KEY
)

print("Upload successful!")
print(f"Bucket: {result['bucket']}")
print(f"Object: {result['object_key']}")

exists = s3_service.file_exists(S3_OBJECT_KEY)

print(f"File exists in S3: {exists}")
