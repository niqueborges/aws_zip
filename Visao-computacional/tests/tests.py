import unittest

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))
from app import app  # Importando o app onde as rotas estão definidas

class TestVisionV1(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_vision_v1_emotion(self):
        # Simula o POST de uma imagem com uma face
        payload = {
            "bucket": "myphotos",
            "imageName": "test-happy.jpg"
        }
        response = self.app.post('/v1/vision', json=payload)
        
        # Testa se o status code é 200
        self.assertEqual(response.status_code, 200)
        
        # Valida se o retorno contém os campos esperados
        data = response.get_json()
        self.assertIn("faces", data)
        self.assertIn("url_to_image", data)
        
        # Verifica se a emoção foi classificada corretamente
        face = data["faces"][0]
        self.assertEqual(face["classified_emotion"], "HAPPY")
        self.assertGreater(face["classified_emotion_confidence"], 90)

    def test_vision_v1_no_face(self):
        # Simula o POST de uma imagem sem face
        payload = {
            "bucket": "myphotos",
            "imageName": "no-face.jpg"
        }
        response = self.app.post('/v1/vision', json=payload)
        
        # Testa se o status code é 200
        self.assertEqual(response.status_code, 200)
        
        # Valida se o retorno está no formato correto quando não há face
        data = response.get_json()
        self.assertEqual(data["faces"][0]["classified_emotion"], None)
        self.assertEqual(data["faces"][0]["classified_emotion_confidence"], None)

if __name__ == '__main__':
    unittest.main()