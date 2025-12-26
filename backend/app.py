from fastapi import FastAPI, Request, Depends, HTTPException, status, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, init_db, test_connection, User, Prediction
from auth import router as auth_router
from auth_utils import get_current_active_user
from pydantic import BaseModel
from typing import Optional
import joblib
import pandas as pd
import numpy as np
import uvicorn
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="Loan Prediction System",
    description="ML-powered loan approval prediction with authentication",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for images
app.mount("/images", StaticFiles(directory="images"), name="images")

# Include authentication router
app.include_router(auth_router)

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print(" Starting Loan Prediction System...")
    print(" Initializing database...")
    
    if test_connection():
        init_db()
        print(" Database initialized successfully!")
    else:
        print(" Database connection failed!")

# Load ML Model
print(" Loading ML model...")
try:
    model = joblib.load('model.pkl')
    scaler = joblib.load('scaler.pkl')
    label_encoders = joblib.load('label_encoders.pkl')
    feature_names = joblib.load('feature_names.pkl')
    print(" Model loaded successfully!")
except Exception as e:
    print(f" Error loading model: {e}")
    model = None

# Pydantic Models
class PredictionRequest(BaseModel):
    name: Optional[str] = None
    annual_income: float
    debt_to_income_ratio: float
    credit_score: int
    loan_amount: float
    interest_rate: float
    gender: str
    marital_status: str
    education_level: str
    employment_status: str
    loan_purpose: str
    grade_subgrade: str

class PredictionResponse(BaseModel):
    prediction: str
    prediction_value: int
    approval_probability: float
    rejection_probability: float

# Serve static files (HTML, CSS, JS)
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Redirect to login page"""
    return FileResponse('../frontend/login.html')

@app.get("/login.html", response_class=HTMLResponse)
async def login_page():
    return FileResponse('../frontend/login.html')

@app.get("/register.html", response_class=HTMLResponse)
async def register_page():
    return FileResponse('../frontend/register.html')

@app.get("/forgot-password.html", response_class=HTMLResponse)
async def forgot_password_page():
    return FileResponse('../frontend/forgot-password.html')

@app.get("/reset-password.html", response_class=HTMLResponse)
async def reset_password_page():
    return FileResponse('../frontend/reset-password.html')

@app.get("/index.html", response_class=HTMLResponse)
async def index_page():
    return FileResponse('../frontend/index.html')

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "database_connected": test_connection()
    }

# Prediction endpoint (protected)
@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Make loan prediction (requires authentication)"""
    
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML model not loaded"
        )
    
    try:
        # Create DataFrame
        test_data = pd.DataFrame({
            'annual_income': [request.annual_income],
            'debt_to_income_ratio': [request.debt_to_income_ratio],
            'credit_score': [request.credit_score],
            'loan_amount': [request.loan_amount],
            'interest_rate': [request.interest_rate],
            'gender': [request.gender],
            'marital_status': [request.marital_status],
            'education_level': [request.education_level],
            'employment_status': [request.employment_status],
            'loan_purpose': [request.loan_purpose],
            'grade_subgrade': [request.grade_subgrade]
        })
        
        # Encode categorical features
        categorical_features = ['gender', 'marital_status', 'education_level', 
                               'employment_status', 'loan_purpose', 'grade_subgrade']
        
        for col in categorical_features:
            if col in label_encoders:
                le = label_encoders[col]
                try:
                    test_data[col] = le.transform(test_data[col])
                except ValueError:
                    test_data[col] = 0
        
        # Ensure column order
        test_data = test_data[feature_names]
        
        # Scale features
        test_data_scaled = scaler.transform(test_data)
        
        # Make prediction
        prediction = model.predict(test_data_scaled)[0]
        prediction_proba = model.predict_proba(test_data_scaled)[0]
        
        # Save prediction to database
        db_prediction = Prediction(
            name=request.name,
            annual_income=request.annual_income,
            debt_to_income_ratio=request.debt_to_income_ratio,
            credit_score=request.credit_score,
            loan_amount=request.loan_amount,
            interest_rate=request.interest_rate,
            gender=request.gender,
            marital_status=request.marital_status,
            education_level=request.education_level,
            employment_status=request.employment_status,
            loan_purpose=request.loan_purpose,
            grade_subgrade=request.grade_subgrade,
            prediction=int(prediction),
            probability=float(prediction_proba[1]),
            user_id=current_user.id
        )
        db.add(db_prediction)
        db.commit()
        
        result = {
            'prediction': 'APPROVED' if prediction == 1 else 'REJECTED',
            'prediction_value': int(prediction),
            'approval_probability': float(prediction_proba[1]),
            'rejection_probability': float(prediction_proba[0])
        }
        
        print(f" Prediction made for user {current_user.username}: {result['prediction']}")
        return result
        
    except Exception as e:
        print(f" Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )

# Get user's prediction history
@app.get("/predictions/history")
async def get_prediction_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    predictions = db.query(Prediction).filter(
        Prediction.user_id == current_user.id
    ).order_by(Prediction.created_at.desc()).all()
    
    return {
        "total": len(predictions),
        "predictions": [
            {
                "id": pred.id,
                "name": pred.name,
                "prediction": "APPROVED" if pred.prediction == 1 else "REJECTED",
                "probability": pred.probability,
                "annual_income": pred.annual_income,
                "loan_amount": pred.loan_amount,
                "credit_score": pred.credit_score,
                "debt_to_income_ratio": pred.debt_to_income_ratio,
                "interest_rate": pred.interest_rate,
                "gender": pred.gender,
                "marital_status": pred.marital_status,
                "education_level": pred.education_level,
                "employment_status": pred.employment_status,
                "loan_purpose": pred.loan_purpose,
                "grade_subgrade": pred.grade_subgrade,
                "created_at": pred.created_at
            }
            for pred in predictions
        ]
    }


# Helper function to safely convert values
def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        if pd.isna(value) or value == '' or value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to int"""
    try:
        if pd.isna(value) or value == '' or value is None:
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_str(value, default='Unknown'):
    """Safely convert value to string"""
    try:
        if pd.isna(value) or value == '' or value is None:
            return default
        return str(value).strip()
    except (ValueError, TypeError):
        return default

# Batch prediction endpoint (protected) - FIXED VERSION
@app.post("/batch_predict")
async def batch_predict(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Handle batch predictions from CSV (requires authentication)"""
    
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML model not loaded"
        )
    
    try:
        # Read CSV
        import io
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Replace NaN with empty strings first
        df = df.fillna('')
        
        print(f" Processing {len(df)} applicants from CSV")
        print(f" Columns: {df.columns.tolist()}")
        
        predictions = []
        saved_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Safely extract and convert values
                name = safe_str(row.get('name', ''), f"Applicant_{idx+1}")
                annual_income = safe_float(row.get('annual_income', 0))
                debt_to_income = safe_float(row.get('debt_to_income_ratio', 0))
                credit_score = safe_int(row.get('credit_score', 0))
                loan_amount = safe_float(row.get('loan_amount', 0))
                interest_rate = safe_float(row.get('interest_rate', 0))
                gender = safe_str(row.get('gender', ''), 'Male')
                marital = safe_str(row.get('marital_status', ''), 'Single')
                education = safe_str(row.get('education_level', ''), 'Bachelor')
                employment = safe_str(row.get('employment_status', ''), 'Employed')
                purpose = safe_str(row.get('loan_purpose', ''), 'Personal')
                grade = safe_str(row.get('grade_subgrade', ''), 'B1')
                
                print(f"Row {idx}: {name}, Income: {annual_income}, Loan: {loan_amount}")
                
                # Skip if critical values are 0
                if annual_income == 0 or loan_amount == 0:
                    print(f" Skipping row {idx} - missing critical data")
                    error_count += 1
                    continue
                
                # Create prediction
                test_data = pd.DataFrame({
                    'annual_income': [annual_income],
                    'debt_to_income_ratio': [debt_to_income],
                    'credit_score': [credit_score],
                    'loan_amount': [loan_amount],
                    'interest_rate': [interest_rate],
                    'gender': [gender],
                    'marital_status': [marital],
                    'education_level': [education],
                    'employment_status': [employment],
                    'loan_purpose': [purpose],
                    'grade_subgrade': [grade]
                })
                
                # Encode and scale
                for col in ['gender', 'marital_status', 'education_level', 
                           'employment_status', 'loan_purpose', 'grade_subgrade']:
                    if col in label_encoders:
                        try:
                            test_data[col] = label_encoders[col].transform(test_data[col])
                        except:
                            test_data[col] = 0
                
                test_data = test_data[feature_names]
                test_data_scaled = scaler.transform(test_data)
                
                prediction = model.predict(test_data_scaled)[0]
                prediction_proba = model.predict_proba(test_data_scaled)[0]
                
                # Save to database with proper data types
                db_prediction = Prediction(
                    name=name,
                    annual_income=float(annual_income),
                    debt_to_income_ratio=float(debt_to_income),
                    credit_score=int(credit_score),
                    loan_amount=float(loan_amount),
                    interest_rate=float(interest_rate),
                    gender=str(gender),
                    marital_status=str(marital),
                    education_level=str(education),
                    employment_status=str(employment),
                    loan_purpose=str(purpose),
                    grade_subgrade=str(grade),
                    prediction=int(prediction),
                    probability=float(prediction_proba[1]),
                    user_id=current_user.id
                )
                db.add(db_prediction)
                db.flush()  # Flush to catch any database errors early
                saved_count += 1
                
                predictions.append({
                    'name': name,
                    'prediction': 'APPROVED' if prediction == 1 else 'REJECTED',
                    'approval_probability': float(prediction_proba[1]),
                    'rejection_probability': float(prediction_proba[0]),
                    'annual_income': float(annual_income),
                    'loan_amount': float(loan_amount),
                    'credit_score': int(credit_score),
                    'debt_to_income_ratio': float(debt_to_income),
                    'interest_rate': float(interest_rate),
                    'gender': str(gender),
                    'marital_status': str(marital),
                    'education_level': str(education),
                    'employment_status': str(employment),
                    'loan_purpose': str(purpose),
                    'grade_subgrade': str(grade)
                })
                
            except Exception as row_error:
                error_count += 1
                print(f" Error processing row {idx}: {row_error}")
                continue
        
        # Commit all predictions to database
        db.commit()
        
        approved = sum(1 for p in predictions if p['prediction'] == 'APPROVED')
        rejected = len(predictions) - approved
        
        print(f" Batch prediction complete: {saved_count} saved, {error_count} errors")
        print(f"   Results: {approved} approved, {rejected} rejected")
        
        return {
            'predictions': predictions,
            'summary': {
                'total': len(predictions),
                'approved': approved,
                'rejected': rejected,
                'approval_rate': (approved / len(predictions) * 100) if len(predictions) > 0 else 0,
                'saved': saved_count,
                'errors': error_count
            }
        }
        
    except Exception as e:
        db.rollback()
        print(f" Batch prediction error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch prediction error: {str(e)}"
        )

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" Loan Prediction System with Authentication Starting...")
    print("="*70)
    print(" API Server: http://127.0.0.1:8000")
    print(" API Docs: http://127.0.0.1:8000/docs")
    print(" Login Page: http://127.0.0.1:8000/login.html")
    print("="*70)
    print(" Authentication Endpoints:")
    print("   POST /auth/register - Register new user")
    print("   POST /auth/login - Login user")
    print("   POST /auth/forgot-password - Request password reset")
    print("   POST /auth/reset-password - Reset password")
    print("   GET  /auth/me - Get current user")
    print("="*70)
    print(" Prediction Endpoints (Protected):")
    print("   POST /predict - Single prediction")
    print("   POST /batch_predict - Batch predictions (saved to DB)")
    print("   GET  /predictions/history - Get prediction history")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000)