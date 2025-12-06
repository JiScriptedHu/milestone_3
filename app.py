from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
import pickle
import os

# --------------------------
# UPDATED PATHS
# --------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "Bengaluru_house_price_cleaned.csv")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Tell Flask where templates and static files are now stored
app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR),
    static_folder=os.path.join(FRONTEND_DIR, "static")
)

# Global variables
model = None
scaler = None
label_encoders = {}
feature_cols = []

def train_model():
    """Train the model on Ready To Move properties only"""
    global model, scaler, label_encoders, feature_cols
    
    print("="*60)
    print("TRAINING MODEL - READY TO MOVE PROPERTIES ONLY")
    print("="*60)
    
    # Load dataset (UPDATED PATH)
    df = pd.read_csv(DATA_PATH)
    print(f"Total records in dataset: {len(df)}")
    
    # Filter only "Ready To Move" properties
    df = df[df['availability'] == 'Ready To Move'].copy()
    print(f"Records after filtering 'Ready To Move': {len(df)}")
    
    # Preprocessing
    df['society'] = df['society'].fillna('Unknown')
    df['bath'] = df['bath'].fillna(df['bath'].median())
    df['balcony'] = df['balcony'].fillna(df['balcony'].median())
    
    # Convert total_sqft (handle ranges like "2100-2850")
    def convert_sqft(x):
        if pd.isna(x):
            return np.nan
        x = str(x).strip()
        if '-' in x:
            parts = x.split('-')
            try:
                return (float(parts[0]) + float(parts[1])) / 2
            except:
                return np.nan
        try:
            return float(x)
        except:
            return np.nan
    
    df['total_sqft'] = df['total_sqft'].apply(convert_sqft)
    df['total_sqft'] = df['total_sqft'].fillna(df['total_sqft'].median())
    
    # Extract BHK
    def extract_bhk(x):
        if pd.isna(x):
            return np.nan
        x = str(x).strip()
        if 'BHK' in x or 'RK' in x:
            return int(x.split()[0])
        elif 'Bedroom' in x:
            return int(x.split()[0])
        else:
            return np.nan
    
    df['bhk'] = df['size'].apply(extract_bhk)
    df['bhk'] = df['bhk'].fillna(df['bhk'].median())
    
    # price per sqft
    df['price_per_sqft'] = df['price'] * 100000 / df['total_sqft']
    
    # Outlier removal
    print("Removing outliers...")
    initial_count = len(df)
    df = df[(df['price_per_sqft'] >= df['price_per_sqft'].quantile(0.01)) & 
            (df['price_per_sqft'] <= df['price_per_sqft'].quantile(0.99))]
    df = df[df['total_sqft']/df['bhk'] >= 300]
    print(f"Records after removing outliers: {len(df)} (removed {initial_count - len(df)})")
    
    # Encode features
    categorical_features = ['location', 'area_type', 'availability', 'zone_name']
    numerical_features = ['total_sqft', 'bath', 'balcony', 'bhk']
    
    print("\nEncoding categorical features...")
    for col in categorical_features:
        le = LabelEncoder()
        df[col + '_encoded'] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le
        print(f"  {col}: {len(le.classes_)} unique values")
    
    # Prepare features
    feature_cols = [col + '_encoded' for col in categorical_features] + numerical_features
    X = df[feature_cols]
    y = df['price']
    
    print(f"\nFeatures: {len(feature_cols)}")
    print(f"Samples: {len(X)}")
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    print("\nTraining Random Forest model...")
    model = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    model.fit(X_train_scaled, y_train)
    
    # Evaluation
    print(f"\nTraining R²: {model.score(X_train_scaled, y_train):.3f}")
    print(f"Test R²: {model.score(X_test_scaled, y_test):.3f}")
    
    # Save model files
    print("\nSaving model files...")
    pickle.dump(model, open('model.pkl', 'wb'))
    pickle.dump(scaler, open('scaler.pkl', 'wb'))
    pickle.dump(label_encoders, open('label_encoders.pkl', 'wb'))
    pickle.dump(feature_cols, open('feature_cols.pkl', 'wb'))

    print("MODEL TRAINING COMPLETED!")
    return df


def load_model():
    """Load trained model and artifacts"""
    global model, scaler, label_encoders, feature_cols
    
    try:
        model = pickle.load(open('model.pkl', 'rb'))
        scaler = pickle.load(open('scaler.pkl', 'rb'))
        label_encoders = pickle.load(open('label_encoders.pkl', 'rb'))
        feature_cols = pickle.load(open('feature_cols.pkl', 'rb'))
        print("✓ Model loaded successfully")
        return True
    except FileNotFoundError:
        print("⚠ Model files not found. Training new model…")
        return False


def get_unique_values():
    """Get unique dropdown values"""
    df = pd.read_csv(DATA_PATH)
    df = df[df['availability'] == 'Ready To Move']
    
    return {
        'locations': sorted(df['location'].dropna().unique().tolist()),
        'area_types': sorted(df['area_type'].dropna().unique().tolist()),
        'zones': sorted(df['zone_name'].dropna().unique().tolist())
    }

# --------------------------
# SERVE FRONTEND
# --------------------------
@app.route('/')
def home():
    unique_values = get_unique_values()

    df = pd.read_csv(DATA_PATH)
    df = df[df['availability'] == 'Ready To Move']
    dataset_combinations = df[['location', 'area_type', 'availability', 'zone_name']].to_dict('records')

    return render_template(
        'index.html',
        locations=unique_values['locations'],
        area_types=unique_values['area_types'],
        zones=unique_values['zones'],
        dataset_json=dataset_combinations
    )

# --------------------------
# PREDICT ROUTE
# --------------------------
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        if data.get('availability') != 'Ready To Move':
            return jsonify({'success': False, 'error': 'Only Ready To Move supported'})
        
        input_data = {
            'location_encoded': label_encoders['location'].transform([data['location']])[0],
            'area_type_encoded': label_encoders['area_type'].transform([data['area_type']])[0],
            'availability_encoded': label_encoders['availability'].transform([data['availability']])[0],
            'zone_name_encoded': label_encoders['zone_name'].transform([data['zone_name']])[0],
            'total_sqft': float(data['total_sqft']),
            'bath': int(data['bath']),
            'balcony': int(data['balcony']),
            'bhk': int(data['bhk'])
        }

        input_df = pd.DataFrame([input_data])[feature_cols]
        input_scaled = scaler.transform(input_df)
        prediction = model.predict(input_scaled)[0]

        pps = (prediction * 100000) / float(data['total_sqft'])

        return jsonify({
            'success': True,
            'predicted_price': round(prediction, 2),
            'price_in_crores': round(prediction / 100, 2),
            'price_per_sqft': round(pps, 2)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# --------------------------
# RETRAIN
# --------------------------
@app.route('/retrain', methods=['POST'])
def retrain():
    try:
        train_model()
        load_model()
        return jsonify({'success': True, 'message': 'Model retrained successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# --------------------------
# RUN APP
# --------------------------
if __name__ == '__main__':
    print("\n" + "="*60)
    print("BANGALORE HOUSE PRICE PREDICTOR")
    print("="*60 + "\n")

    if not all(os.path.exists(f) for f in ['model.pkl', 'scaler.pkl', 'label_encoders.pkl', 'feature_cols.pkl']):
        print("No model found—training new one.")
        train_model()
    
    load_model()
    
    print("Server running at: http://localhost:5000\n")
    
    app.run(debug=True, port=5000)