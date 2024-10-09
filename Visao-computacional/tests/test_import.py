import unittest
import sys
import os

# Ajusta o caminho do sistema para garantir que o 'app' seja importado corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestImport(unittest.TestCase):

    def test_import_app(self):
        try:
            from app import app  # Tenta importar a instância do Flask
        except ImportError:
            self.fail("Não foi possível importar 'app'")

if __name__ == '__main__':
    unittest.main()


