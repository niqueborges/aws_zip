import os
import shutil


def clean_cache() -> None:
    """Remove __pycache__ and .pytest_cache directories."""
    cache_dirs = ["__pycache__", ".pytest_cache"]
    
    for root, dirs, _ in os.walk("."):
        for cache_dir in cache_dirs:
            if cache_dir in dirs:
                cache_path = os.path.join(root, cache_dir)
                try:
                    shutil.rmtree(cache_path)
                    print(f"Removed: {cache_path}")
                except Exception as e:
                    print(f"Failed to remove {cache_path}: {e}")


if __name__ == "__main__":
    clean_cache()
