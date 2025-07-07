# weather_predictor/app/main.py
import sys
import os
import csv
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QScrollArea
)
from PyQt5.QtGui import QFont, QPixmap, QMovie
from PyQt5.QtCore import Qt, QSize, QTimer 

# Import des modules locaux
from app.weather_api import fetch_weather_data 
import joblib 
import pandas as pd 

# --- Chemins des fichiers et dossiers ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBSERVATIONS_DIR = os.path.join(BASE_DIR, 'data', 'observations')
OBSERVATIONS_FILE = os.path.join(OBSERVATIONS_DIR, 'temperature_observations.csv')
MODELS_DIR = os.path.join(BASE_DIR, 'data', 'models')
ICONS_DIR = os.path.join(BASE_DIR, 'assets', 'icons') # Chemin des icônes

# S'assurer que les dossiers existent
os.makedirs(OBSERVATIONS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(ICONS_DIR, exist_ok=True) # S'assurer que le dossier des icônes existe

class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prédiction Météo Locale")
        self.showMaximized() 

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f4f8; 
                font-family: Arial, sans-serif;
            }
            QLabel {
                color: #334e68; 
                font-size: 14px;
            }
            QLineEdit {
                border: 1px solid #aebfd4; 
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                background-color: #ffffff;
                color: black;
            }
            #cityInput { 
                min-width: 250px;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            }
            #weatherInfoFrame { 
                background-color: #e0e7ee; 
                border: 1px solid #aebfd4;
            }
            .infoLabel {
                font-size: 16px;
                margin-bottom: 5px;
            }
            .tempLabel {
                font-size: 18px;
                font-weight: bold;
                color: #007bff;
            }
            .probLabel {
                font-size: 16px;
                color: #666;
            }
            #dateTimeLabel { 
                font-size: 14px;
                font-weight: bold;
                color: #555;
                margin-bottom: 10px;
            }
            #weatherIconLabel { 
                /* Les propriétés de taille min/max sont mieux gérées par setFixedSize en Python */
                /* margin: 10px auto; pour le centrage horizontal via le layout parent */
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 5px;
                background-color: #ffffff;
            }
            #cityDisplayLabel { 
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)

        self.init_ui()
        self.load_model() 
        self.start_clock() 

    def init_ui(self):
        main_layout = QVBoxLayout(self) 

        self.scroll_area = QScrollArea(self) 
        self.scroll_area.setWidgetResizable(True) 
        
        self.scroll_content_widget = QWidget() 
        self.scroll_content_layout = QVBoxLayout(self.scroll_content_widget) 
        self.scroll_content_layout.setContentsMargins(20, 20, 20, 20)
        self.scroll_content_layout.setSpacing(15)

        # Date et Heure Actuelles
        self.date_time_label = QLabel()
        self.date_time_label.setObjectName("dateTimeLabel")
        self.date_time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.scroll_content_layout.addWidget(self.date_time_label)

        # Zone de recherche
        search_layout = QHBoxLayout()
        search_layout.setAlignment(Qt.AlignCenter)
        
        self.city_label = QLabel("Entrez le nom de la ville:")
        self.city_label.setFont(QFont("Arial", 12))
        search_layout.addWidget(self.city_label)

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Ex: Paris, Londres...")
        self.city_input.setObjectName("cityInput")
        self.city_input.returnPressed.connect(self.get_weather) 
        search_layout.addWidget(self.city_input)

        self.search_button = QPushButton("Rechercher")
        self.search_button.clicked.connect(self.get_weather)
        search_layout.addWidget(self.search_button)

        self.scroll_content_layout.addLayout(search_layout)

        # Cadre d'informations météo
        self.weather_info_frame = QFrame()
        self.weather_info_frame.setObjectName("weatherInfoFrame")
        weather_layout = QVBoxLayout()
        weather_layout.setAlignment(Qt.AlignCenter)

        self.city_display_label = QLabel("Météo pour [Ville], [Pays]")
        self.city_display_label.setObjectName("cityDisplayLabel") 
        self.city_display_label.setAlignment(Qt.AlignCenter)
        weather_layout.addWidget(self.city_display_label)

        # Label pour l'icône météo - CORRECTION ICI
        self.weather_icon_label = QLabel()
        self.weather_icon_label.setObjectName("weatherIconLabel")
        self.weather_icon_label.setAlignment(Qt.AlignCenter)
        # Définir une taille fixe appropriée pour l'icône, en tenant compte du padding et du border
        # L'icône de 64x64 + 2*padding(5) + 2*border(2) = 64 + 10 + 4 = 78x78.
        # Donc, 80x80 est une bonne taille de label pour une icône de 64x64.
        self.weather_icon_label.setFixedSize(80, 80) 
        # setScaledContents(True) est essentiel pour que l'image s'adapte au label
        self.weather_icon_label.setScaledContents(True) 
        weather_layout.addWidget(self.weather_icon_label)
        
        weather_layout.addSpacing(15)

        # Demain
        self.temp_demain_label = QLabel("Temp. Max Demain: --°C (Modèle) | --°C (API)")
        self.temp_demain_label.setObjectName("tempLabel")
        weather_layout.addWidget(self.temp_demain_label)

        self.prob_pluie_demain_label = QLabel("Probabilité de Pluie Demain: --%")
        self.prob_pluie_demain_label.setObjectName("probLabel")
        weather_layout.addWidget(self.prob_pluie_demain_label)

        self.humidity_demain_label = QLabel("Humidité Demain: --%")
        self.humidity_demain_label.setObjectName("infoLabel")
        weather_layout.addWidget(self.humidity_demain_label)

        self.pressure_demain_label = QLabel("Pression Demain: -- hPa")
        self.pressure_demain_label.setObjectName("infoLabel")
        weather_layout.addWidget(self.pressure_demain_label)

        self.wind_speed_demain_label = QLabel("Vent Demain: -- m/s")
        self.wind_speed_demain_label.setObjectName("infoLabel")
        weather_layout.addWidget(self.wind_speed_demain_label)
        
        weather_layout.addSpacing(15)
        weather_layout.addWidget(self.create_separator()) 

        # Après-demain
        self.temp_apres_demain_label = QLabel("Temp. Max Après-Demain: --°C")
        self.temp_apres_demain_label.setObjectName("tempLabel")
        weather_layout.addWidget(self.temp_apres_demain_label)

        self.prob_pluie_apres_demain_label = QLabel("Probabilité de Pluie Après-Demain: --%")
        self.prob_pluie_apres_demain_label.setObjectName("probLabel")
        weather_layout.addWidget(self.prob_pluie_apres_demain_label)

        self.humidity_apres_demain_label = QLabel("Humidité Après-Demain: --%")
        self.humidity_apres_demain_label.setObjectName("infoLabel")
        weather_layout.addWidget(self.humidity_apres_demain_label)

        self.pressure_apres_demain_label = QLabel("Pression Après-Demain: -- hPa")
        self.pressure_apres_demain_label.setObjectName("infoLabel")
        weather_layout.addWidget(self.pressure_apres_demain_label)

        self.wind_speed_apres_demain_label = QLabel("Vent Après-Demain: -- m/s")
        self.wind_speed_apres_demain_label.setObjectName("infoLabel")
        weather_layout.addWidget(self.wind_speed_apres_demain_label)

        self.weather_info_frame.setLayout(weather_layout)
        self.scroll_content_layout.addWidget(self.weather_info_frame)
        
        self.done_label = QLabel("Terminé")
        self.done_label.setAlignment(Qt.AlignCenter)
        self.done_label.setStyleSheet("color: #28a745; font-weight: bold; font-size: 16px;")
        self.scroll_content_layout.addWidget(self.done_label)

        self.scroll_area.setWidget(self.scroll_content_widget)
        main_layout.addWidget(self.scroll_area)
        
        self.clear_weather_display()

    def create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #e0e0e0;")
        return separator

    def start_clock(self):
        self.update_time() 
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000) 

    def update_time(self):
        current_datetime = datetime.now()
        jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        
        jour_semaine = jours[current_datetime.weekday()]
        nom_mois = mois[current_datetime.month - 1]
        
        self.date_time_label.setText(current_datetime.strftime(f"{jour_semaine} %d {nom_mois} %Y - %H:%M:%S"))

    def clear_weather_display(self):
        self.city_display_label.setText("Météo pour [Ville], [Pays]")
        self.temp_demain_label.setText("Temp. Max Demain: --°C (Modèle) | --°C (API)")
        self.prob_pluie_demain_label.setText("Probabilité de Pluie Demain: --%")
        self.humidity_demain_label.setText("Humidité Demain: --%")
        self.pressure_demain_label.setText("Pression Demain: -- hPa")
        self.wind_speed_demain_label.setText("Vent Demain: -- m/s")

        self.temp_apres_demain_label.setText("Temp. Max Après-Demain: --°C")
        self.prob_pluie_apres_demain_label.setText("Probabilité de Pluie Après-Demain: --%")
        self.humidity_apres_demain_label.setText("Humidité Après-Demain: --%")
        self.pressure_apres_demain_label.setText("Pression Après-Demain: -- hPa")
        self.wind_speed_apres_demain_label.setText("Vent Après-Demain: -- m/s")
        
        # Réinitialiser les icônes à l'état par défaut
        self.set_weather_icon_display(None, self.weather_icon_label)

    def get_icon_pixmap(self, icon_filename, size=64):
        """
        Charge une QPixmap à partir d'un fichier icône, gère les erreurs et le redimensionnement.
        """
        icon_path = os.path.join(ICONS_DIR, icon_filename)
        print(f"Tentative de chargement de l'icône: {icon_path}")

        pixmap = QPixmap()
        if os.path.exists(icon_path) and pixmap.load(icon_path):
            print(f"Icône chargée avec succès: {icon_filename}")
            # Ne pas redimensionner ici, laisser setScaledContents(True) le faire dans le QLabel
            # Ou alors, redimensionner ici à la taille exacte voulue (64x64)
            return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            if not os.path.exists(icon_path):
                print(f"Erreur: Fichier icône non trouvé: {icon_path}")
            else:
                print(f"Erreur: QPixmap n'a pas pu charger {icon_path}. Fichier peut-être corrompu, format non supporté, ou permissions.")
            return QPixmap() # Retourne une QPixmap nulle

    def set_weather_icon_display(self, prob_pluie, target_label):
        """
        Définit l'icône appropriée sur le QLabel cible en fonction de la probabilité de pluie.
        """
        # --- Étape 1: Nettoyer l'état précédent du QLabel ---
        # Arrêter tout QMovie (GIF) s'il y en a un
        if target_label.movie():
            target_label.movie().stop()
            target_label.setMovie(None)
        # Effacer tout contenu (image ou texte)
        target_label.clear()
        
        # --- Étape 2: Gérer l'icône de chargement (GIF) ---
        if prob_pluie == 'loading':
            loading_path = os.path.join(ICONS_DIR, 'loading.gif')
            if os.path.exists(loading_path):
                movie = QMovie(loading_path)
                if movie.isValid():
                    # Utiliser la taille du QLabel pour le redimensionnement du GIF
                    movie.setScaledSize(target_label.size()) 
                    target_label.setMovie(movie)
                    movie.start()
                    print("GIF de chargement démarré.")
                else:
                    print(f"Erreur: GIF de chargement invalide: {loading_path}")
                    target_label.setText("...")
            else:
                print(f"Erreur: Fichier GIF de chargement non trouvé: {loading_path}")
                target_label.setText("...")
            return

        # --- Étape 3: Déterminer et charger l'icône statique (PNG/SVG) ---
        prob_int = -1
        if isinstance(prob_pluie, str) and prob_pluie.endswith('%'):
            try:
                prob_int = int(prob_pluie.replace('%', ''))
            except ValueError:
                pass

        icon_filename = "default.png" # Icône par défaut

        if prob_int >= 70:
            icon_filename = "heavy_rain.png"
        elif prob_int >= 40:
            icon_filename = "rain.png"
        elif prob_int >= 0:
            icon_filename = "sun.png"

        # Tenter de charger le pixmap avec la taille du label
        # Ici, nous utilisons directement la taille du label (80x80) pour la pixmap,
        # puis setScaledContents(True) l'adaptera au label si nécessaire.
        final_pixmap = self.get_icon_pixmap(icon_filename, size=target_label.width()) 

        # --- Étape 4: Afficher le pixmap ou un indicateur d'erreur ---
        if not final_pixmap.isNull():
            target_label.setPixmap(final_pixmap)
            print(f"Icône '{icon_filename}' affichée sur le label.")
        else:
            # Si l'icône spécifique n'a pas pu être chargée, tenter l'icône par défaut
            default_pixmap = self.get_icon_pixmap("default.png", size=target_label.width())
            if not default_pixmap.isNull():
                target_label.setPixmap(default_pixmap)
                print("Icône par défaut affichée.")
            else:
                target_label.setText("?")
                print(f"Avertissement: Impossible d'afficher l'icône. Ni '{icon_filename}' ni 'default.png' n'ont pu être chargés.")


    def load_model(self):
        """Charge le modèle de prédiction le plus récent."""
        self.model = None
        model_files = [f for f in os.listdir(MODELS_DIR) if f.endswith('.pkl')]
        if not model_files:
            print("Aucun modèle trouvé. Le modèle ML ne sera pas utilisé.")
            return

        model_files.sort(key=lambda x: os.path.getmtime(os.path.join(MODELS_DIR, x)), reverse=True)
        latest_model_path = os.path.join(MODELS_DIR, model_files[0])

        try:
            self.model = joblib.load(latest_model_path)
            print(f"Modèle chargé: {latest_model_path}")
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            self.model = None

    def predict_with_model(self, temp_predite_modele_prev, date_prevision, humidity_api, pressure_api, wind_speed_api):
        """
        Fait une prédiction avec le modèle chargé en utilisant toutes les features pertinentes.
        """
        if self.model:
            try:
                day_of_year = date_prevision.timetuple().tm_yday
                month = date_prevision.month
                day_of_week = date_prevision.weekday() 

                input_data = pd.DataFrame([[
                    temp_predite_modele_prev,
                    humidity_api,
                    pressure_api,
                    wind_speed_api,
                    day_of_year,
                    month,
                    day_of_week
                ]],
                columns=['temp_predite_modele', 'humidity_api', 'pressure_api', 'wind_speed_api', 'day_of_year', 'month', 'day_of_week'])
                
                prediction = self.model.predict(input_data)[0]
                return round(float(prediction), 1) 
            except Exception as e:
                print(f"Erreur lors de la prédiction avec le modèle : {e}")
                return None
        return None 

    def save_observation(self, city, date_prediction, predicted_temp_model, observed_temp_api, humidity_api, pressure_api, wind_speed_api):
        """
        Sauvegarde une observation dans un fichier CSV.
        """
        file_exists = os.path.exists(OBSERVATIONS_FILE)

        try:
            with open(OBSERVATIONS_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow([
                        'date_enregistrement', 'ville', 'date_prevision', 
                        'temp_predite_modele', 'temp_observee_api', 
                        'humidity_api', 'pressure_api', 'wind_speed_api'
                    ])
                
                date_enregistrement = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([
                    date_enregistrement, city, date_prediction.strftime('%Y-%m-%d'), 
                    predicted_temp_model, observed_temp_api, 
                    humidity_api, pressure_api, wind_speed_api
                ])
            print(f"Observation sauvegardée pour {city} le {date_prediction.strftime('%Y-%m-%d')}.")
        except Exception as e:
            QMessageBox.warning(self, "Erreur de Sauvegarde", f"Impossible de sauvegarder l'observation : {e}")
            print(f"Erreur de sauvegarde: {e}")

    def get_weather(self):
        city_name = self.city_input.text().strip()
        if not city_name:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer le nom d'une ville.")
            return

        self.city_display_label.setText(f"Météo pour {city_name}...")
        self.clear_weather_display() 
        self.set_weather_icon_display('loading', self.weather_icon_label) 

        api_data = fetch_weather_data(city_name)
        
        if api_data and api_data["temp_max_demain"] is not None:
            temp_api_demain = api_data.get("temp_max_demain")
            prob_pluie_demain = api_data.get("prob_pluie_demain")
            humidity_demain = api_data.get("humidity_demain")
            pressure_demain = api_data.get("pressure_demain")
            wind_speed_demain = api_data.get("wind_speed_demain")

            temp_api_apres_demain = api_data.get("temp_max_apres_demain")
            prob_pluie_apres_demain = api_data.get("prob_pluie_apres_demain")
            humidity_apres_demain = api_data.get("humidity_apres_demain")
            pressure_apres_demain = api_data.get("pressure_apres_demain")
            wind_speed_apres_demain = api_data.get("wind_speed_apres_demain")

            date_demain = datetime.now().date() + timedelta(days=1)
            date_apres_demain = datetime.now().date() + timedelta(days=2)

            temp_modele_demain = self.predict_with_model(
                temp_api_demain, 
                date_demain,
                humidity_demain, 
                pressure_demain, 
                wind_speed_demain
            )
            
            model_status_text = "N/A (modèle non dispo)"
            temp_modele_demain_display = temp_api_demain 
            if temp_modele_demain is not None:
                temp_modele_demain_display = temp_modele_demain
                model_status_text = "Modèle"

            self.city_display_label.setText(f"Météo pour {city_name}")
            
            self.temp_demain_label.setText(
                f"Temp. Max Demain: {temp_modele_demain_display}°C ({model_status_text}) | {temp_api_demain}°C (API)"
            )
            
            self.prob_pluie_demain_label.setText(f"Probabilité de Pluie Demain: {prob_pluie_demain if prob_pluie_demain is not None else '--'}%")
            self.humidity_demain_label.setText(f"Humidité Demain: {humidity_demain if humidity_demain is not None else '--'}%")
            self.pressure_demain_label.setText(f"Pression Demain: {pressure_demain if pressure_demain is not None else '--'} hPa")
            self.wind_speed_demain_label.setText(f"Vent Demain: {wind_speed_demain if wind_speed_demain is not None else '--'} m/s")
            
            self.temp_apres_demain_label.setText(f"Temp. Max Après-Demain: {temp_api_apres_demain if temp_api_apres_demain is not None else '--'}°C")
            self.prob_pluie_apres_demain_label.setText(f"Probabilité de Pluie Après-Demain: {prob_pluie_apres_demain if prob_pluie_apres_demain is not None else '--'}%")
            self.humidity_apres_demain_label.setText(f"Humidité Après-Demain: {humidity_apres_demain if humidity_apres_demain is not None else '--'}%")
            self.pressure_apres_demain_label.setText(f"Pression Après-Demain: {pressure_apres_demain if pressure_apres_demain is not None else '--'} hPa")
            self.wind_speed_apres_demain_label.setText(f"Vent Après-Demain: {wind_speed_apres_demain if wind_speed_apres_demain is not None else '--'} m/s")

            # Appliquer les icônes
            self.set_weather_icon_display(f"{prob_pluie_demain}%" if prob_pluie_demain is not None else 'N/A', self.weather_icon_label)

            self.save_observation(
                city_name, date_demain, temp_modele_demain_display, temp_api_demain,
                humidity_demain, pressure_demain, wind_speed_demain
            )
            
            if temp_api_apres_demain is not None:
                self.save_observation(
                    city_name, date_apres_demain, temp_api_apres_demain, temp_api_apres_demain, 
                    humidity_apres_demain, pressure_apres_demain, wind_speed_apres_demain
                )

        else:
            self.city_display_label.setText(f"Météo pour {city_name} (Données non trouvées)")
            self.clear_weather_display()
            QMessageBox.information(self, "Données Météo", f"Impossible de récupérer les données météo pour {city_name}. Vérifiez le nom de la ville ou votre clé API.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec_())