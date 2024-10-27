from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import onnxruntime as ort
from transformers import AutoTokenizer
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
import os

# Initialize FastAPI app
app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the tokenizer
try:
    model_name = "prajjwal1/bert-tiny"  # Replace with the correct model name if needed
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    print("Tokenizer loaded successfully.")
except Exception as e:
    print("Error loading tokenizer:", str(e))
    raise HTTPException(status_code=500, detail="Error loading tokenizer")

# Load the ONNX model
onnx_model_path = "/Users/sameehrazak/Downloads/AIVM/backserver/bert_spam_detection.onnx"  # Update this path

if not os.path.exists(onnx_model_path):
    print("ONNX model file not found at:", onnx_model_path)
    raise HTTPException(status_code=500, detail="ONNX model file not found")

try:
    session = ort.InferenceSession(onnx_model_path)
    print("ONNX model loaded successfully.")
except Exception as e:
    print("Error loading ONNX model:", str(e))
    raise HTTPException(status_code=500, detail="Error loading ONNX model")

# Define data model for request
class EmailRequest(BaseModel):
    content: str

# Define the function to perform inference
def classify_email_onnx(text):
    try:
        # Tokenize input text
        inputs = tokenizer(
            text,
            max_length=128,
            padding="max_length",
            truncation=True,
            return_tensors="np"
        )
        print("Tokenized input:", inputs)

        # Convert input_ids and attention_mask to int64 for ONNX compatibility
        onnx_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64)
        }
        print("ONNX model inputs:", onnx_inputs)

        # Run inference
        logits = session.run(None, onnx_inputs)[0]

        # Get prediction
        predicted_label = np.argmax(logits, axis=1)[0]
        return "Spam" if predicted_label == 1 else "Ham"
    except Exception as e:
        print("Error during model inference:", str(e))
        raise HTTPException(status_code=500, detail="Error processing the model")

# Endpoint to classify email
@app.post("/classify-email/")
async def classify_email(request: EmailRequest):
    try:
        # Perform inference
        classification = classify_email_onnx(request.content)
        return {"classification": classification}
    except Exception as e:
        print("Error in classify_email endpoint:", str(e))
        raise HTTPException(status_code=500, detail="Error processing the model") from e

# Uncomment and adjust the following section if you need to upload the model
# import aivm_client as aic

# Define the model name and file path
# MODEL_NAME = "bert_spam_detection"
# onnx_model_path = "/Users/sameehrazak/Downloads/AIVM/backserver/bert_spam_detection.onnx"

# Upload the model to the AIVM server
# aic.upload_bert_tiny_model(onnx_model_path, MODEL_NAME)
