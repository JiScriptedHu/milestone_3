import pandas as pd
import numpy as np

def clean_data(input_file, output_file):
    print(f"Reading data from {input_file}...")
    df = pd.read_csv(input_file)
    print(f"Original shape: {df.shape}")

    # 1. Filter only "Ready To Move" properties
    df = df[df['availability'] == 'Ready To Move'].copy()
    print(f"After filtering 'Ready To Move': {df.shape}")

    # 2. Handle Missing Values
    df['society'] = df['society'].fillna('Unknown')
    df['bath'] = df['bath'].fillna(df['bath'].median())
    df['balcony'] = df['balcony'].fillna(df['balcony'].median())

    # 3. Convert total_sqft (handle ranges like "2100-2850")
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

    # 4. Extract BHK from size column
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

    # 5. Create price_per_sqft for outlier detection
    # Price is in lakhs, so multiply by 100,000
    df['price_per_sqft'] = df['price'] * 100000 / df['total_sqft']

    # 6. Remove Outliers
    print("Removing outliers...")
    
    # Remove rows where price_per_sqft is extremely low or high (1st and 99th percentile)
    min_threshold = df['price_per_sqft'].quantile(0.01)
    max_threshold = df['price_per_sqft'].quantile(0.99)
    df = df[(df['price_per_sqft'] >= min_threshold) & (df['price_per_sqft'] <= max_threshold)]
    
    # Remove rows where sqft per bedroom is less than 300 (impractical size)
    df = df[df['total_sqft'] / df['bhk'] >= 300]
    
    print(f"Final shape after cleaning: {df.shape}")

    # 7. Save to CSV
    # We drop 'price_per_sqft' if you don't want it in the final file, 
    # but keeping it is often useful for analysis. 
    # Comment out the next line if you want to keep it.
    # df = df.drop(columns=['price_per_sqft']) 
    
    df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to {output_file}")

if __name__ == "__main__":
    input_csv = 'Bengaluru_house_price_zoned.csv'
    output_csv = 'Bengaluru_house_price_cleaned.csv'
    
    try:
        clean_data(input_csv, output_csv)
    except FileNotFoundError:
        print(f"Error: The file '{input_csv}' was not found. Please check the file path.")