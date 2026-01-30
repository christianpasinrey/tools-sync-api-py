from beanie import Document


class DeletionLog(Document):
    user_id: str
    store_name: str
    item_id: str
    deleted_at: int  # Timestamp in milliseconds

    class Settings:
        name = "deletionlogs"
        indexes = [
            [("user_id", 1), ("deleted_at", 1)],
        ]
