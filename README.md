# House Price Predictor

A Machine Learning web application that estimates property values in Bangalore using a **Random Forest Regressor** served via **Flask**.

**Key Features:**
* **Real-Time Predictions:** Enter property details (Location, BHK, Sq. Ft, etc.) to get an instant valuation in Lakhs and Crores.
* **Smart Filtering:** Focuses specifically on "Ready To Move" properties for accurate current market analysis.
* **Self-Training:** Automatically retrains the model on startup if no pre-existing model is detected.
* **Responsive UI:** Clean, interactive frontend built with HTML/CSS and JavaScript.

## How to Use

1. Allow script execution for the current process
```bash
Set-ExecutionPolicy Unrestricted -Scope Process
```

2. Create the virtual environment
```bash
python -m venv venv
```

3. Activate the environment
```bash
.\venv\Scripts\activate
```

4. Install the required dependencies:
```bash
pip install -r requirements.txt
```

5. Run the applicaton
```bash
python app.py
```

6. Open your browser and navigate to
```bash
http://localhost:5000
```

<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/b4991442-9681-45c0-93a2-12dc0ee23d1f" />
