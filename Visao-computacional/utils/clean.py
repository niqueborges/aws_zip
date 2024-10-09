import os
import shutil

def clean_cache() -> None:
    """Remove os diretórios __pycache__ e .pytest_cache."""
    cache_dirs = ["__pycache__", ".pytest_cache"]
    
    # Percorre todos os diretórios e subdiretórios a partir do diretório atual
    for root, dirs, _ in os.walk("."):
        for cache_dir in cache_dirs:
            if cache_dir in dirs:
                cache_path = os.path.join(root, cache_dir)
                try:
                    # Remove o diretório de cache
                    shutil.rmtree(cache_path)
                    print(f"Removido: {cache_path}")
                except Exception as e:
                    print(f"Falha ao remover {cache_path}: {e}")

if __name__ == "__main__":
    clean_cache()
