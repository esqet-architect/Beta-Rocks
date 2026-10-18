#!/usr/bin/env python3
"""
ESQET CORE: Local Multi-Modal Fusion Engine (Offline)
Uses TFLite for local vision inference.
Fuses ResNet embeddings with physical sensor telemetry.
"""
import os
import numpy as np
from PIL import Image

# Try to load TFLite runtime
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite

class FossilTFLiteClassifier:
    def __init__(self, model_path="models/mobilenet_v1_1.0_224.tflite"):
        self.model_path = os.path.expanduser(f"~/Beta-Rocks/{model_path}")
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at {self.model_path}. Run wget first.")
            
        self.interpreter = tflite.Interpreter(model_path=self.model_path)
        self.interpreter.allocate_tensors()
        
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        self.input_shape = self.input_details[0]['shape']

    def load_and_preprocess_image(self, image_path):
        img = Image.open(image_path).convert('RGB')
        img = img.resize((self.input_shape[1], self.input_shape[2]))
        img_array = np.array(img, dtype=np.float32)
        # Normalize to [-1, 1] for MobileNet
        img_array = (img_array / 127.5) - 1.0
        return np.expand_dims(img_array, axis=0)

    def predict_local(self, image_path, telemetry):
        """Runs the local model and fuses with sensor data."""
        input_data = self.load_and_preprocess_image(image_path)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        vision_class_id = np.argmax(output_data)
        vision_confidence = np.max(output_data)
        
        # --- THE FUSION HEAD ---
        # Combine vision with physics
        magnetic = telemetry.get("magnetic_uT", 0)
        fractal_dim = telemetry.get("fractal_dimension", 1.0)
        
        decision = "UNRESOLVED"
        evidence = []
        
        # Example fusion logic
        if vision_confidence > 0.5:
            evidence.append(f"Vision suggests class {vision_class_id}")
            
        if magnetic > 100:
            evidence.append("High magnetic anomaly (Ferrous)")
            decision = "IRON-RICH MINERAL"
            
        if fractal_dim < 1.2:
            evidence.append("Smooth edge geometry")
            if magnetic < 50:
                decision = "GLASS / OBSIDIAN"
        elif fractal_dim > 1.6:
            evidence.append("Rough, chaotic edge geometry")
            decision = "CRUMBLED AGGREGATE"

        return {
            "local_inference": True,
            "vision_class": int(vision_class_id),
            "vision_confidence": float(vision_confidence),
            "fusion_decision": decision,
            "evidence_chain": evidence,
            "fractal_dim": round(fractal_dim, 4),
            "magnetic_uT": magnetic
        }

if __name__ == "__main__":
    # Test it locally
    classifier = FossilTFLiteClassifier()
    print("TFLite Engine Online.")
    
    # We use a dummy image path if the user doesn't have one, 
    # but the logic is real.
    test_telemetry = {"magnetic_uT": 120.0, "fractal_dimension": 1.15}
    # result = classifier.predict_local("/path/to/real/image.jpg", test_telemetry)
    # print(result)
