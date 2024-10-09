import unittest
import sys
import os

# Ajusta o caminho do sistema para garantir que o 'app' seja importado corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app import app  # Aqui deve estar correto
except ImportError:
    raise ImportError("Não foi possível importar 'app'. Verifique se o caminho está correto.")

class TestVisionV2(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_vision_v2_pet(self):
        payload = {
            "bucket": "myphotos",
            "imageName": "cao-pastor.jpg"  # Alteramos para uma imagem de cão pastor
        }
        response = self.app.post('/v2/vision', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("pets", data)
        self.assertIn("url_to_image", data)
        pet = data["pets"][0]
        self.assertIn("Dicas", pet)
        self.assertIn("Nível de Energia e Necessidades de Exercícios", pet["Dicas"])
        self.assertIn("Temperamento e Comportamento", pet["Dicas"])

    def test_vision_v2_no_pet(self):
        payload = {
            "bucket": "myphotos",
            "imageName": "no-pet.jpg"
        }
        response = self.app.post('/v2/vision', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertNotIn("pets", data)

if __name__ == '__main__':
    unittest.main()
