import logging
import shutil
from pathlib import Path
import fsspec
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from adt_eval.types import AzureStorageConfig

# Silence noisy loggers
logging.getLogger("fsspec").setLevel(logging.ERROR)
logging.getLogger("adlfs").setLevel(logging.ERROR)
logging.getLogger("azure").setLevel(logging.ERROR)


class ImageDownloader:
    """Download images from Azure Blob Storage efficiently.

    Uses fsspec for remote access and ``shutil.copyfileobj`` for
    memory-efficient streaming. Also supports concurrent batch
    downloads for higher throughput.
    """

    def __init__(self, image_dir: str, azure_storage_config: AzureStorageConfig):
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.azure_storage_config = azure_storage_config

    def download_azure_image(self, image_url: str, filename: str) -> Path:
        """Download a single image from Azure Blob Storage.

        The file is streamed from Azure to disk without loading the
        entire content into memory.
        """

        # Adjust URL scheme for fsspec compatibility
        formatted_url = image_url.replace("azure-blob", "az")
        local_path = self.image_dir / filename

        if local_path.exists():
            logging.debug(f"Image '{local_path}' already exists, skipping download.")
            return local_path

        try:
            with fsspec.open(
                formatted_url,
                account_name=self.azure_storage_config.account_name,
                account_key=self.azure_storage_config.account_key,
            ) as remote_file:
                with open(local_path, "wb") as local_file:
                    shutil.copyfileobj(remote_file, local_file)

            logging.debug(f"Downloaded image '{local_path}'.")
            return local_path

        except Exception as e:
            logging.error(f"Error downloading {formatted_url}: {e}")

            # Remove partial file if an error occurred
            if local_path.exists():
                local_path.unlink()

            raise

    def download_batch(self, items, max_workers: int = 8) -> list[Path]:
        """Download many images concurrently with a CLI progress bar.

        Args:
            items: Iterable of entries, where each entry is either:
                - a tuple ``(image_url, filename)``, or
                - a dict with keys ``{"url", "filename"}``.
            max_workers: Maximum number of parallel download threads.

        Returns:
            List of ``Path`` objects for successfully downloaded files.
        """

        # Materialize items so we can know the total for the progress bar
        items = list(items)
        total_files = len(items)

        def parse_item(item):
            if isinstance(item, dict):
                return item["url"], item["filename"]
            # Assume (url, filename) tuple-like
            return item

        def worker(item):
            url, fname = parse_item(item)
            try:
                item['local_path'] = self.download_azure_image(url, fname)
                return item
            except Exception as exc:  # noqa: BLE001
                logging.error(f"Failed to download {url}: {exc}")
                return None

        results: list[Path] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker, item) for item in items]

            # Progress bar tracks successfully downloaded files
            with tqdm(total=total_files, desc="Downloading images", unit="file") as pbar:
                for future in as_completed(futures):
                    path = future.result()
                    if path is not None:
                        results.append(path)
                        pbar.update(1)

        return results
