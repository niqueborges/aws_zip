import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

class TestVisionV2(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_vision_v2_pet(self):
        # Simula o POST de uma imagem com um pet
        payload = {
            "bucket": "myphotos",
            "imageName": "labrador.jpg"
        }
        response = self.app.post('/v2/vision', json=payload)
        
        # Testa se o status code é 200
        self.assertEqual(response.status_code, 200)
        
        # Valida se o retorno contém os campos esperados
        data = response.get_json()
        self.assertIn("pets", data)
        self.assertIn("url_to_image", data)
        
        # Verifica se as dicas do pet foram retornadas
        pet = data["pets"][0]
        self.assertIn("Dicas", pet)
        self.assertIn("Nível de Energia e Necessidades de Exercícios", pet["Dicas"])
        self.assertIn("Temperamento e Comportamento", pet["Dicas"])

    def test_vision_v2_no_pet(self):
        # Simula o POST de uma imagem sem pet
        payload = {
            "bucket": "myphotos",
            "imageName": "no-pet.jpg"
        }
        response = self.app.post('/v2/vision', json=payload)
        
        # Testa se o status code é 200
        self.assertEqual(response.status_code, 200)
        
        # Verifica se o retorno não contém a chave 'pets'
        data = response.get_json()
        self.assertNotIn("pets", data)
        
if __name__ == '__main__':
    unittest.main()