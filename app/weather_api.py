import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv


load_dotenv()

# Récupérer la clé API
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"

def fetch_weather_data(city_name):
    """
    Récupère les données de prévision météo pour une ville donnée.
    Retourne la température maximale, probabilité de pluie, humidité, pression
    et vitesse du vent pour demain et après-demain.
    """
    if OPENWEATHER_API_KEY == "VOTRE_CLE_API_OPENWEATHERMAP" or not OPENWEATHER_API_KEY:
        print("ATTENTION: Clé API OpenWeatherMap non configurée ou invalide. Utilisation de données factices.")
        # Données factices pour permettre au script de fonctionner sans clé API
        if city_name.lower() == "lyon":
            return {
                "temp_max_demain": 15.0, # API observation
                "prob_pluie_demain": 15,
                "humidity_demain": 70,    # Donnée factice
                "pressure_demain": 1012,  # Donnée factice
                "wind_speed_demain": 5.0, # Donnée factice

                "temp_max_apres_demain": 25.0, # API observation
                "prob_pluie_apres_demain": 50,
                "humidity_apres_demain": 65,    # Donnée factice
                "pressure_apres_demain": 1010,  # Donnée factice
                "wind_speed_apres_demain": 7.0  # Donnée factice
            }
        else:
            return None # Pour les autres villes sans clé API, on ne peut pas simuler

    params = {
        "q": city_name,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric", # Celsius
        "lang": "fr"
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP
        data = response.json()

        # Calculer les dates pour demain et après-demain
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        day_after_tomorrow = today + timedelta(days=2)

        # Initialisation des variables pour demain
        temp_max_demain = None
        prob_pluie_demain = None
        humidity_demain = None
        pressure_demain = None
        wind_speed_demain = None

        # Initialisation des variables pour après-demain
        temp_max_apres_demain = None
        prob_pluie_apres_demain = None
        humidity_apres_demain = None
        pressure_apres_demain = None
        wind_speed_apres_demain = None

        # Parcourir les prévisions par tranches de 3 heures
        for forecast in data.get('list', []):
            forecast_time = datetime.fromtimestamp(forecast['dt']).date()
            
            # Données principales
            main_data = forecast.get('main', {})
            wind_data = forecast.get('wind', {})

            # Température maximale pour la journée (on prend la plus élevée)
            current_temp_max = main_data.get('temp_max')
            # Probabilité de précipitation (pop) est entre 0 et 1
            current_pop = forecast.get('pop', 0) * 100 
            current_humidity = main_data.get('humidity')
            current_pressure = main_data.get('pressure')
            current_wind_speed = wind_data.get('speed')

            if forecast_time == tomorrow:
                if temp_max_demain is None or (current_temp_max is not None and current_temp_max > temp_max_demain):
                    temp_max_demain = current_temp_max
                if prob_pluie_demain is None or current_pop > prob_pluie_demain:
                    prob_pluie_demain = current_pop
                # Pour humidité, pression, vent, on prend la valeur de la prévision de midi ou la moyenne
                # Pour cet exemple, on prend la dernière valeur trouvée pour le jour
                if current_humidity is not None: humidity_demain = current_humidity
                if current_pressure is not None: pressure_demain = current_pressure
                if current_wind_speed is not None: wind_speed_demain = current_wind_speed

            elif forecast_time == day_after_tomorrow:
                if temp_max_apres_demain is None or (current_temp_max is not None and current_temp_max > temp_max_apres_demain):
                    temp_max_apres_demain = current_temp_max
                if prob_pluie_apres_demain is None or current_pop > prob_pluie_apres_demain:
                    prob_pluie_apres_demain = current_pop
                if current_humidity is not None: humidity_apres_demain = current_humidity
                if current_pressure is not None: pressure_apres_demain = current_pressure
                if current_wind_speed is not None: wind_speed_apres_demain = current_wind_speed

        return {
            "temp_max_demain": temp_max_demain,
            "prob_pluie_demain": int(prob_pluie_demain) if prob_pluie_demain is not None else None,
            "humidity_demain": humidity_demain,
            "pressure_demain": pressure_demain,
            "wind_speed_demain": wind_speed_demain,

            "temp_max_apres_demain": temp_max_apres_demain,
            "prob_pluie_apres_demain": int(prob_pluie_apres_demain) if prob_pluie_apres_demain is not None else None,
            "humidity_apres_demain": humidity_apres_demain,
            "pressure_apres_demain": pressure_apres_demain,
            "wind_speed_apres_demain": wind_speed_apres_demain
        }

    except requests.exceptions.RequestException as e:
        print(f"Erreur de connexion à l'API météo : {e}")
        return None
    except KeyError as e:
        print(f"Erreur dans les données de l'API (clé manquante) : {e}")
        return None
    except Exception as e:
        print(f"Une erreur inattendue est survenue : {e}")
        return None

if __name__ == "__main__":
    # Test rapide du module
    print("Test de la récupération des données météo pour Lyon...")
    data = fetch_weather_data("Lyon")
    if data:
        print(f"Température max demain (API): {data['temp_max_demain']}°C")
        print(f"Probabilité pluie demain (API): {data['prob_pluie_demain']}%")
        print(f"Humidité demain (API): {data['humidity_demain']}%")
        print(f"Pression demain (API): {data['pressure_demain']} hPa")
        print(f"Vitesse vent demain (API): {data['wind_speed_demain']} m/s")
    else:
        print("Échec de la récupération des données de test.")