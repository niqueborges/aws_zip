import os

def clean_terminal():
    """Limpa o terminal: Windows/Linux."""
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    clean_terminal()
