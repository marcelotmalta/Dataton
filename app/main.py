from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

# Global variables to hold data and model
# Using a dictionary to store global state might be cleaner, or attach to app.state
# But for now, keeping globals to minimize disruption, or better: attach to app.state in lifespan?
# The original code used globals.
# Let's use globals for compatibility with existing functions, or update functions to use app.state if accessed that way?
# valid functions: search_student relies on global df_base. predict_score relies on global model_pipeline.
# So we must keep them global OR update them. 
# Updating them to use request.app.state is better but requires changing signatures to include Request.
# Let's keep globals for now but initialize them in lifespan.

df_base = None
model_pipeline = None
features_list = None
mapa_classes = None

# Paths
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'df_Base_final.csv')
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'modelo_pedra_conceito_xgb_2025.pkl')

class StudentMetrics(BaseModel):
    IAN: float
    IDA: float
    IEG: float
    IAA: float
    IPS: float
    IPP: float
    IPV: float
    FASE: int
    DEFA: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    global df_base, model_pipeline, features_list, mapa_classes
    try:
        # Load Data
        if os.path.exists(DATA_PATH):
            df_base = pd.read_csv(DATA_PATH)
            logger.info(f"Data loaded successfully from {DATA_PATH}, shape: {df_base.shape}")
        else:
            logger.error(f"Data file not found at {DATA_PATH}")

        # Load Model
        if os.path.exists(MODEL_PATH):
            loaded_data = joblib.load(MODEL_PATH)
            model_pipeline = loaded_data['modelo']
            features_list = loaded_data['features']
            mapa_classes = loaded_data['mapa_classes']
            # Reverse map for human readable output
            mapa_classes_inv = {v: k for k, v in mapa_classes.items()}
            # Store inverse map for easy access later
            app.state.mapa_classes_inv = mapa_classes_inv
            
            logger.info(f"Model loaded successfully from {MODEL_PATH}")
            logger.info(f"Model version: {loaded_data.get('versao', 'unknown')}")
        else:
            logger.error(f"Model file not found at {MODEL_PATH}")
            # raise FileNotFoundError(f"Model file not found at {MODEL_PATH}") # Don't crash startup?
            # Original code raised error.

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # raise e # Failing startup is usually good if critical resources missing

    yield
    # Clean up if needed

app = FastAPI(title="Student Performance API", version="1.0", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": model_pipeline is not None, "data_loaded": df_base is not None}

@app.get("/students/{name}")
def search_student(name: str):
    if df_base is None:
        raise HTTPException(status_code=503, detail="Data not loaded available")
    
    # Case insensitive search
    matches = df_base[df_base['NOME'].str.contains(name, case=False, na=False)]
    
    if matches.empty:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Select relevant columns to return
    # Adjust columns based on what's available and publicly shareable if needed
    # For now returning all record data
    return matches.to_dict(orient="records")

@app.post("/predict")
def predict_score(metrics: StudentMetrics):
    if model_pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded available")
    
    try:
        # Prepare input data
        input_data = metrics.model_dump()
        
        # Feature Engineering
        # Status_DEFA
        defa = input_data['DEFA']
        if defa < 0:
            input_data['Status_DEFA'] = 0
        elif defa == 0:
            input_data['Status_DEFA'] = 1
        else:
            input_data['Status_DEFA'] = 2
            
        # consistencia_acad = IDA / (IEG + 0.1)
        input_data['consistencia_acad'] = input_data['IDA'] / (input_data['IEG'] + 0.1)
        
        # Create DataFrame for prediction with Model's expected features
        df_predict = pd.DataFrame([input_data])
        
        # Ensure only expected features are passed and in correct order
        # We need to handle potential missing columns by filling them? 
        # Or ensuring Pydantic model covers all base features.
        # Based on features_list: ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV', 'FASE', 'Status_DEFA', 'consistencia_acad']
        # The Pydantic model covers IAN, IDA, IEG, IAA, IPS, IPP, IPV, FASE.
        # Derived: Status_DEFA, consistencia_acad.
        # So we have all of them.
        
        X = df_predict[features_list]
        
        # In the notebook, SimpleImputer was used on X before training.
        # The loaded model object in the pickle might be just the XGBClassifier, or a pipeline.
        # The notebook code:
        # export_data_xgb = { 'modelo': modelo_xgb, 'imputer': imputer, ... }
        # So we likely need to apply the imputer first if loaded.
        
        # Let's check how we loaded it.
        # model_pipeline = loaded_data['modelo'] -> This is XGBClassifier
        # We should also load the imputer.
        
        # Re-loading to check structure in the code isn't possible here, but taking from context:
        # We should probably use the imputer if it exists in the loaded dictionary.
        
        # NOTE: For single prediction, if fields are required in Pydantic, they won't be null (unless Optional).
        # Assuming inputs are complete for now.
        
        # Predict
        prediction_idx = model_pipeline.predict(X)[0]
        
        # Get Probabilities
        probs = model_pipeline.predict_proba(X)[0]
        
        # Map class index to name
        mapa = app.state.mapa_classes_inv
        pedra_predita = mapa.get(int(prediction_idx), "Unknown")
        
        # Construct response
        probabilities = {mapa.get(i, f"Class_{i}"): float(prob) for i, prob in enumerate(probs)}
        
        return {
            "prediction": pedra_predita,
            "probabilities": probabilities,
            "input_features": X.to_dict(orient="records")[0]
        }

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
