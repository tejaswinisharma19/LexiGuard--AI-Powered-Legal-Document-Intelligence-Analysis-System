import os
import sys

sys.path.insert(0, os.path.abspath("."))
from services.postgresql_service import PostgreSQLService


def main():

    service = PostgreSQLService()

    test_document_id = (
        "e28d55ce-c219-4cb2-93bf-255f7bb666d7"
    )

    try:
        if not service.get_document(test_document_id):
            service.save_document({
                "document_id": test_document_id,
                "filename": "test_analysis_doc.pdf",
                "user_id": "test_user@example.com"
            })

        test_history_entry = {
            "analysis_id": "test_analysis_001",
            "analysis_type": "qa",
            "question": (
                "What is the monthly payment?"
            ),
            "response": (
                "The monthly payment is ₹75,000."
            ),
            "sources": [
                {
                    "page_number": 1,
                    "chunk_number": 2
                }
            ],
            "timestamp": (
                "2026-09-18T11:30:00+05:30"
            )
        }

        service.add_analysis_history(
            test_document_id,
            test_history_entry
        )

        history = service.get_analysis_history(
            test_document_id
        )

        assert history is not None

        assert len(history) >= 1

        latest_entry = history[-1]

        assert (
            latest_entry["analysis_id"]
            == "test_analysis_001"
        )

        assert (
            latest_entry["analysis_type"]
            == "qa"
        )

        assert (
            latest_entry["question"]
            == "What is the monthly payment?"
        )

        assert (
            latest_entry["sources"][0]["page_number"]
            == 1
        )

        print(
            "PASS: Analysis history saved"
        )

        print(
            "PASS: Analysis history retrieved"
        )

        print(
            "PASS: Analysis history fields verified"
        )
    finally:
        service.delete_document(test_document_id)


if __name__ == "__main__":
    main()