import os
import logging
from typing import Dict, Any, Optional
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# Standard Indian Biomedical Waste Categories
STANDARD_CATEGORIES = {
    "YELLOW": {
        "name": "Infectious & Anatomical Waste",
        "bin_color": "Yellow",
        "bin_color_hex": "#ffc107",
        "badge_class": "bg-warning text-dark",
        "container": "Non-chlorinated Yellow plastic bag",
        "treatment": "Incineration or Plasma Pyrolysis / Deep Burial",
        "items": "Human tissues, organs, soiled cotton, plaster casts, blood bags, expired drugs"
    },
    "RED": {
        "name": "Contaminated Recyclable Plastics",
        "bin_color": "Red",
        "bin_color_hex": "#dc3545",
        "badge_class": "bg-danger text-white",
        "container": "Non-chlorinated Red plastic bag",
        "treatment": "Autoclaving/Microwaving followed by shredding and recycling",
        "items": "Disposable tubing, bottles, intravenous tubes, catheters, syringes without needles, gloves"
    },
    "WHITE": {
        "name": "Waste Sharps including Metals",
        "bin_color": "White / Translucent",
        "bin_color_hex": "#e2e8f0",
        "badge_class": "bg-light text-dark border border-secondary",
        "container": "Puncture-proof, tamper-proof, leak-proof container",
        "treatment": "Autoclaving or Dry Heat Sterilization followed by shredding / encapsulation",
        "items": "Needles, scalpels, blades, contaminated sharp objects, burn needle tips"
    },
    "BLUE": {
        "name": "Glassware and Metallic Implants",
        "bin_color": "Blue",
        "bin_color_hex": "#0d6efd",
        "badge_class": "bg-primary text-white",
        "container": "Puncture-proof and leak-proof card/plastic box with blue marking",
        "treatment": "Disinfection (sodium hypochlorite) or autoclaving followed by recycling",
        "items": "Broken medicine vials, ampoules, glass bottles, orthopedic metallic implants"
    },
    "GENERAL": {
        "name": "General Non-Infectious Waste",
        "bin_color": "Black / Green",
        "bin_color_hex": "#212529",
        "badge_class": "bg-dark text-white",
        "container": "Standard black / green municipal dustbin bag",
        "treatment": "Municipal solid waste disposal or composting",
        "items": "Office paper, non-infected packaging, food waste, water bottles"
    },
    "UNKNOWN": {
        "name": "Unknown / Needs Manual Review",
        "bin_color": "Grey / Orange",
        "bin_color_hex": "#6c757d",
        "badge_class": "bg-secondary text-white",
        "container": "Isolated holding container for Infection Officer inspection",
        "treatment": "Mandatory manual safety inspection by Infection Control Officer",
        "items": "Unidentified residue, mixed waste, damaged containers requiring protocol evaluation"
    }
}

class MedicalWasteClassifier:
    """
    AI Medical Waste Classifier with MobileNetV2 architecture support
    and transparent educational heuristic demo fallback.
    """
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.75):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.is_tf_available = False
        self._initialize_backend()

    def _initialize_backend(self):
        """Check for TensorFlow installation and load weights if available."""
        try:
            import tensorflow as tf
            self.is_tf_available = True
            if self.model_path and os.path.exists(self.model_path):
                self.model = tf.keras.models.load_model(self.model_path)
                logger.info(f"Loaded trained MobileNetV2 weights from {self.model_path}")
            else:
                logger.info("TensorFlow is installed, but no pre-trained weights file was found. Operating in educational demonstration mode.")
        except ImportError:
            self.is_tf_available = False
            logger.info("TensorFlow is not present in the runtime environment. Using the transparent Educational Heuristic Classifier.")

    def classify_image(self, image_path: str) -> Dict[str, Any]:
        """
        Classifies medical waste image.
        Returns prediction details, confidence, safety flags, and BMW 2016 disposal instructions.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at path: {image_path}")

        # If TensorFlow and trained model are available, use model inference
        if self.is_tf_available and self.model is not None:
            return self._classify_with_tensorflow(image_path)
        else:
            return self._classify_with_demo_heuristic(image_path)

    def _classify_with_tensorflow(self, image_path: str) -> Dict[str, Any]:
        """Inference with TensorFlow MobileNetV2."""
        import tensorflow as tf
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
        
        img = Image.open(image_path).convert("RGB").resize((224, 224))
        arr = np.array(img, dtype=np.float32)
        arr = np.expand_dims(arr, axis=0)
        arr = preprocess_input(arr)
        
        preds = self.model.predict(arr)[0]
        categories = ["YELLOW", "RED", "WHITE", "BLUE", "GENERAL"]
        prob_dict = {cat: float(preds[i]) for i, cat in enumerate(categories) if i < len(preds)}
        
        top_cat = max(prob_dict, key=prob_dict.get)
        confidence = prob_dict[top_cat]
        
        return self._format_result(top_cat, confidence, prob_dict, demo_mode=False)

    def _classify_with_demo_heuristic(self, image_path: str) -> Dict[str, Any]:
        """
        Educational Demo Heuristic Classifier:
        Inspects visual color channels, brightness, and texture variances of the image
        to demonstrate classification logic without generating false accuracy claims.
        """
        with Image.open(image_path) as img:
            rgb_img = img.convert("RGB").resize((128, 128))
            arr = np.array(rgb_img, dtype=np.float32)

        # Calculate average color channels
        r_mean = float(np.mean(arr[:, :, 0]))
        g_mean = float(np.mean(arr[:, :, 1]))
        b_mean = float(np.mean(arr[:, :, 2]))
        std_dev = float(np.std(arr))

        # Heuristic scoring based on dominant optical profiles
        scores = {
            "YELLOW": 0.15,
            "RED": 0.15,
            "WHITE": 0.15,
            "BLUE": 0.15,
            "GENERAL": 0.15,
            "UNKNOWN": 0.10
        }

        # Yellowish (high R, high G, low B - swabs, bandages, anatomical dressings)
        if r_mean > 140 and g_mean > 120 and b_mean < 110:
            scores["YELLOW"] += 0.55
        # Reddish / Orange (catheters, blood tubing, red plastic pouches)
        elif r_mean > 150 and g_mean < 110 and b_mean < 110:
            scores["RED"] += 0.55
        # Bluish / Cyan / Glass transparency (ampoules, vials, saline glass)
        elif b_mean > 140 and (b_mean > r_mean + 20):
            scores["BLUE"] += 0.50
        # High Brightness / Low Variance (translucent plastic, syringes, shiny metallic blades)
        elif r_mean > 180 and g_mean > 180 and b_mean > 180 and std_dev < 45:
            scores["WHITE"] += 0.50
        # Low Brightness / High Variance (general trash, wrappers, cardboard packaging)
        elif r_mean < 90 and g_mean < 90 and b_mean < 90:
            scores["GENERAL"] += 0.45
        else:
            # Ambiguous image -> flag for manual review
            scores["UNKNOWN"] += 0.40

        # Normalize probabilities via softmax-like distribution
        exp_scores = {k: np.exp(v * 2.5) for k, v in scores.items()}
        total_exp = sum(exp_scores.values())
        prob_dict = {k: round(float(v / total_exp), 3) for k, v in exp_scores.items()}

        top_cat = max(prob_dict, key=prob_dict.get)
        confidence = prob_dict[top_cat]

        return self._format_result(top_cat, confidence, prob_dict, demo_mode=True)

    def _format_result(self, category_code: str, confidence: float, prob_dict: Dict[str, float], demo_mode: bool) -> Dict[str, Any]:
        """Format final classification payload with safety guardrails."""
        # Safety gate: If confidence is under threshold, reclassify as UNKNOWN / Needs Manual Review
        needs_review = confidence < self.confidence_threshold or category_code == "UNKNOWN"
        
        effective_category = "UNKNOWN" if needs_review and category_code != "UNKNOWN" and confidence < 0.55 else category_code
        meta = STANDARD_CATEGORIES.get(effective_category, STANDARD_CATEGORIES["UNKNOWN"])

        confidence_tier = "HIGH" if confidence >= self.confidence_threshold else ("MEDIUM" if confidence >= 0.50 else "LOW")

        return {
            "predicted_category": effective_category,
            "category_name": meta["name"],
            "bin_color": meta["bin_color"],
            "bin_color_hex": meta["bin_color_hex"],
            "badge_class": meta["badge_class"],
            "container_type": meta["container"],
            "treatment_method": meta["treatment"],
            "permitted_items": meta["items"],
            "confidence": round(confidence, 3),
            "confidence_percent": f"{round(confidence * 100, 1)}%",
            "confidence_tier": confidence_tier,
            "needs_review": needs_review,
            "probabilities": prob_dict,
            "demo_mode": demo_mode,
            "disclaimer": (
                "Educational Decision-Support System: AI predictions are assistive suggestions only. "
                "Final segregation must be verified by clinical staff in compliance with Bio-Medical Waste Management Rules (2016)."
            )
        }

# Global singleton classifier instance
classifier = MedicalWasteClassifier()
