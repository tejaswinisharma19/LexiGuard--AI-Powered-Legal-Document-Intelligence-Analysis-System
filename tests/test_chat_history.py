import os
import sys

sys.path.insert(0, os.path.abspath("."))
from services.postgresql_service import PostgreSQLService


def main():

    service = PostgreSQLService()

    document_id = (
        "e28d55ce-c219-4cb2-93bf-255f7bb666d7"
    )

    try:
        if not service.get_document(document_id):
            service.save_document({
                "document_id": document_id,
                "filename": "test_chat_doc.pdf",
                "user_id": "test_user@example.com"
            })

        chat_entry = {
            "message_id": "chat_test_001",
            "user_message": (
                "What is the payment amount?"
            ),
            "assistant_response": (
                "The monthly payment is ₹75,000."
            ),
            "sources": [
                {
                    "page_number": 1,
                    "chunk_number": 2
                }
            ],
            "timestamp": (
                "2026-09-18T12:00:00+05:30"
            )
        }

        service.add_chat_message(
            document_id,
            chat_entry
        )

        history = service.get_chat_history(
            document_id
        )

        assert history is not None
        assert len(history) >= 1

        latest = history[-1]

        assert (
            latest["message_id"]
            == "chat_test_001"
        )

        assert (
            latest["user_message"]
            == "What is the payment amount?"
        )

        assert (
            latest["assistant_response"]
            == "The monthly payment is ₹75,000."
        )

        print("PASS: Chat history saved")
        print("PASS: Chat history retrieved")
        print("PASS: Chat history verified")
    finally:
        service.delete_document(document_id)


if __name__ == "__main__":
    main()