# weather_predictor/training/train_model.py

import pandas as pd
import os
import joblib
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor 
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# --- Chemins des fichiers et dossiers ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBSERVATIONS_FILE = os.path.join(BASE_DIR, 'data', 'observations', 'temperature_observations.csv')
MODELS_DIR = os.path.join(BASE_DIR, 'data', 'models')

# S'assurer que le dossier des modèles existe
os.makedirs(MODELS_DIR, exist_ok=True)

def train_and_save_model():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Début du processus d'entraînement du modèle...")
    
    if not os.path.exists(OBSERVATIONS_FILE):
        print(f"Erreur: Le fichier d'observations n'existe pas à {OBSERVATIONS_FILE}. Aucune donnée pour l'entraînement.")
        return

    try:
        df = pd.read_csv(OBSERVATIONS_FILE)
        print(f"Nombre total d'observations lues: {len(df)}")
        
        # Nettoyage et préparation des données
        # On s'assure que toutes les colonnes qu'on va utiliser comme features ou cible existent
        # et n'ont pas de valeurs manquantes.
        required_columns = [
            'temp_predite_modele', 'temp_observee_api', 
            'humidity_api', 'pressure_api', 'wind_speed_api', 
            'date_prevision'
        ]
        
        # Supprimer les lignes où des valeurs cruciales sont manquantes
        df.dropna(subset=required_columns, inplace=True)
        
        if df.empty:
            print("Le fichier d'observations est vide après nettoyage. Impossible d'entraîner le modèle.")
            return

        # --- Ingénierie des caractéristiques basée sur la date ---
        df['date_prevision'] = pd.to_datetime(df['date_prevision'])
        df['day_of_year'] = df['date_prevision'].dt.dayofyear 
        df['month'] = df['date_prevision'].dt.month           
        df['day_of_week'] = df['date_prevision'].dt.dayofweek 

        # Définir les features (X) et la cible (y)
        # NOUVEAU : Inclure les nouvelles colonnes d'humidité, pression, vent dans les features
        X = df[[
            'temp_predite_modele', 
            'humidity_api', 
            'pressure_api', 
            'wind_speed_api', 
            'day_of_year', 
            'month', 
            'day_of_week'
        ]] 
        y = df['temp_observee_api']    # Ce que nous voulons prédire (la température réelle)

        # Séparer les données en ensembles d'entraînement et de test
        if len(df) < 5: 
            print("Pas assez de données (moins de 5) pour diviser en ensembles d'entraînement/test. Entraînement sur toutes les données.")
            X_train, y_train = X, y
            X_test, y_test = pd.DataFrame(), pd.Series() 
        else:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        print(f"Taille de l'ensemble d'entraînement: {len(X_train)} | Taille de l'ensemble de test: {len(X_test)}")
        print(f"Features utilisées: {X.columns.tolist()}") 

        # --- Entraînement du modèle ---
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1) 
        model.fit(X_train, y_train)
        print("Modèle entraîné (RandomForestRegressor).")

        # --- Évaluation du modèle ---
        if not X_test.empty:
            y_pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            print(f"Erreur Absolue Moyenne (MAE) du modèle sur l'ensemble de test: {mae:.2f}°C")
        else:
            print("Aucun ensemble de test pour l'évaluation du MAE.")

        # --- Sauvegarde du modèle ---
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_filename = f'weather_model_{timestamp}.pkl'
        model_path = os.path.join(MODELS_DIR, model_filename)
        
        joblib.dump(model, model_path)
        print(f"Modèle sauvegardé sous: {model_path}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processus d'entraînement terminé.")

    except pd.errors.EmptyDataError:
        print(f"Le fichier {OBSERVATIONS_FILE} est vide. Aucune donnée pour l'entraînement.")
    except Exception as e:
        print(f"Une erreur est survenue lors de l'entraînement du modèle : {e}")

if __name__ == "__main__":
    train_and_save_model()