import os
import shutil
import logging

logger = logging.getLogger("lexiguard")


class LocalStorageService:
    """
    Local file storage service replacing AWS S3.
    Stores and manages uploaded PDF documents inside the local uploads/ directory
    with strict path traversal protection and graceful error handling.
    """

    def __init__(self, upload_folder=None):
        base = upload_folder or os.getenv("UPLOAD_FOLDER", "uploads")
        self.base_dir = os.path.abspath(base)
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_path(self, object_key):
        """
        Safely resolve an object key to an absolute path inside self.base_dir.
        Guards against directory traversal attempts.
        Handles keys specified as:
          - 'documents/file.pdf'
          - 'uploads/documents/file.pdf'
          - absolute path inside base_dir
        """
        if not object_key:
            raise ValueError("Object key cannot be empty.")

        # Check if already an absolute path inside base_dir
        if os.path.isabs(object_key):
            resolved = os.path.abspath(object_key)
            if not resolved.startswith(self.base_dir):
                raise ValueError(f"Path traversal detected: {object_key}")
            return resolved

        # Normalize slashes
        clean_key = object_key.replace("\\", "/").strip("/")

        # Strip upload folder prefix if present (e.g. 'uploads/...')
        base_name = os.path.basename(self.base_dir)
        if clean_key == base_name:
            clean_key = ""
        elif clean_key.startswith(f"{base_name}/"):
            clean_key = clean_key[len(base_name) + 1:]

        resolved = os.path.abspath(os.path.join(self.base_dir, clean_key))
        if not resolved.startswith(self.base_dir):
            raise ValueError(f"Path traversal detected: {object_key}")
        return resolved

    def upload_file(self, file_path, object_key):
        """
        Save/copy a local file into the uploads directory under object_key.

        Args:
            file_path: Source path of the file to store.
            object_key: Relative storage key (e.g., 'documents/hash_file.pdf').

        Returns:
            dict containing bucket and object_key for interface compatibility.
        """
        dest_path = self._resolve_path(object_key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        # If source and destination are the exact same path, do not copy over itself
        if os.path.abspath(file_path) != dest_path:
            shutil.copy2(file_path, dest_path)
        logger.info("Local storage: saved %s to %s", file_path, dest_path)
        return {
            "bucket": "local",
            "object_key": object_key.replace("\\", "/"),
            "file_path": os.path.relpath(dest_path, os.getcwd()).replace("\\", "/")
        }

    def download_file(self, object_key, local_file_path):
        """
        Copy a file from local storage to a specified local destination.

        Args:
            object_key: Storage key to retrieve.
            local_file_path: Destination path where the file should be copied.

        Returns:
            local_file_path.
        """
        src_path = self._resolve_path(object_key)
        if not os.path.isfile(src_path):
            raise FileNotFoundError(f"File not found in local storage: {object_key}")
        dest_abs = os.path.abspath(local_file_path)
        os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
        if src_path != dest_abs:
            shutil.copy2(src_path, dest_abs)
        return local_file_path

    def delete_file(self, object_key):
        """
        Delete a file from local storage. Handles missing files gracefully.

        Args:
            object_key: Storage key to delete.

        Returns:
            True.
        """
        try:
            target_path = self._resolve_path(object_key)
            if os.path.isfile(target_path):
                os.remove(target_path)
                logger.info("Local storage: deleted %s", target_path)
            else:
                logger.warning("Local storage: file already missing %s", target_path)
        except Exception as e:
            logger.warning("Local storage: error deleting %s: %s", object_key, e)
        return True

    def file_exists(self, object_key):
        """
        Check whether a file exists in local storage.

        Args:
            object_key: Storage key.

        Returns:
            True if file exists, False otherwise.
        """
        try:
            target_path = self._resolve_path(object_key)
            return os.path.isfile(target_path)
        except Exception:
            return False
