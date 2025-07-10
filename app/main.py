# weather_predictor/app/main.py
import sys
import os
import csv
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QScrollArea, QSizePolicy # Import QSizePolicy
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
        # Use a fixed size or set a minimum size and allow stretching for better control
        # self.showMaximized() # Replaced with setFixedSize or initial geometry
        self.setGeometry(100, 100, 800, 600) # Initial window size, you can adjust this

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f4f8; /* Light blue-gray background */
                font-family: 'SF Pro Display', 'Arial', sans-serif; /* Closer to iOS font */
            }
            QLabel {
                color: #334e68; /* Dark blue-gray text */
                font-size: 14px;
            }
            QLineEdit {
                border: 1px solid #aebfd4; /* Soft blue-gray border */
                border-radius: 8px; /* More rounded corners */
                padding: 10px 12px; /* Increased padding for height */
                font-size: 16px; /* Slightly larger font */
                background-color: #ffffff;
                color: black;
            }
            #cityInput {
                min-width: 300px; /* Wider input field */
                max-width: 400px; /* Limit max width */
            }
            QPushButton {
                background-color: #007bff; /* Standard blue */
                color: white;
                border: none;
                border-radius: 8px; /* More rounded corners */
                padding: 10px 20px; /* Increased padding for button size */
                font-size: 16px; /* Larger font for button */
                font-weight: bold;
                min-width: 100px; /* Ensure button has minimum width */
            }
            QPushButton:hover {
                background-color: #0056b3; /* Darker blue on hover */
            }
            QFrame#weatherInfoFrame { /* Specific ID for the info box */
                background-color: white;
                border-radius: 10px;
                padding: 25px; /* More padding inside the frame */
                /* box-shadow is not directly supported in QSS, rely on border/background */
                border: 1px solid #d0dbe7; /* Subtle border for separation */
                margin-top: 20px; /* Space above the info frame */
                margin-bottom: 20px;
            }
            #statusLabel { /* New style for the status label */
                font-size: 14px;
                color: #555;
                font-style: italic;
                margin-top: 10px;
                margin-bottom: 10px;
            }
            #weatherIconLabel {
                /* Handled by setFixedSize and setScaledContents in Python */
                border: none; /* No explicit border as in the screenshot */
                background-color: transparent; /* No background for the icon label itself */
                padding: 0px;
            }
            #cityDisplayLabel {
                font-size: 24px; /* Larger font for main city display */
                font-weight: bold;
                color: #2c3e50; /* Darker text */
                margin-bottom: 15px; /* More space below */
            }
            .tempLabel {
                font-size: 18px; /* Consistent temp label size */
                font-weight: bold;
                color: #007bff; /* Blue for temperature */
                margin-bottom: 5px;
            }
            .probLabel, .infoLabel {
                font-size: 16px; /* Standard info label size */
                color: #555;
                margin-bottom: 5px;
            }
            #dateTimeLabel {
                font-size: 14px;
                font-weight: normal; /* Not bold as in original, matches screenshot more */
                color: #777; /* Softer grey */
                margin-bottom: 15px;
            }
        """)

        self.init_ui()
        self.load_model()
        self.start_clock()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter) # Align content to top and center
        main_layout.setContentsMargins(50, 30, 50, 30) # Overall margins

        # Use a QScrollArea for the content to ensure it's scrollable on smaller screens
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # No horizontal scrollbar

        self.scroll_content_widget = QWidget()
        self.scroll_content_layout = QVBoxLayout(self.scroll_content_widget)
        self.scroll_content_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter) # Center content within scroll area
        self.scroll_content_layout.setContentsMargins(0, 0, 0, 0) # No extra margins inside scroll content
        self.scroll_content_layout.setSpacing(15) # Default spacing between elements

        # Date et Heure Actuelles
        self.date_time_label = QLabel()
        self.date_time_label.setObjectName("dateTimeLabel")
        self.date_time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.scroll_content_layout.addWidget(self.date_time_label)

        # Zone de recherche
        search_container = QHBoxLayout() # Use a horizontal layout for input and button
        search_container.setAlignment(Qt.AlignCenter) # Center the search bar horizontally

        city_input_layout = QHBoxLayout() # A horizontal layout for the "Ville" label and QLineEdit
        city_input_layout.setAlignment(Qt.AlignCenter) # Center elements within this mini-layout

        self.city_label = QLabel("Ville") # Changed text to just "Ville" as in screenshot
        self.city_label.setFont(QFont("Arial", 14)) # Slightly larger font for "Ville"
        city_input_layout.addWidget(self.city_label)

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Paris, Lyon, ...") # Updated placeholder text
        self.city_input.setObjectName("cityInput")
        self.city_input.returnPressed.connect(self.get_weather)
        city_input_layout.addWidget(self.city_input)

        search_button_layout = QHBoxLayout() # Layout for the button to ensure it's distinct
        search_button_layout.setAlignment(Qt.AlignCenter)
        self.search_button = QPushButton("Rechercher")
        self.search_button.clicked.connect(self.get_weather)
        search_button_layout.addWidget(self.search_button)

        # Add the input and button layouts to the main search container
        search_container.addLayout(city_input_layout)
        search_container.addSpacing(20) # Space between input and button
        search_container.addLayout(search_button_layout)

        self.scroll_content_layout.addLayout(search_container)

        # Status Label (like the spinning indicator in the screenshot)
        self.status_label = QLabel("Status...") # Initial status text
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.scroll_content_layout.addWidget(self.status_label)


        # Cadre d'informations météo
        self.weather_info_frame = QFrame()
        self.weather_info_frame.setObjectName("weatherInfoFrame")
        # Ensure the frame expands horizontally but stays centered
        self.weather_info_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed) # Fixed height, preferred width

        weather_layout = QVBoxLayout(self.weather_info_frame)
        weather_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter) # Align content to top and center within frame
        weather_layout.setSpacing(10) # Reduced spacing within the info frame

        self.city_display_label = QLabel("Météo pour (Ville)") # Updated initial text
        self.city_display_label.setObjectName("cityDisplayLabel")
        self.city_display_label.setAlignment(Qt.AlignCenter)
        weather_layout.addWidget(self.city_display_label)

        # Label for the weather icon
        self.weather_icon_label = QLabel()
        self.weather_icon_label.setObjectName("weatherIconLabel")
        self.weather_icon_label.setAlignment(Qt.AlignCenter)
        self.weather_icon_label.setFixedSize(70, 70) # Adjusted size slightly to match common icon sizes better
        self.weather_icon_label.setScaledContents(True)
        weather_layout.addWidget(self.weather_icon_label)

        weather_layout.addSpacing(15) # More space before weather details

        # Demain
        self.temp_demain_label = QLabel("Temp. Max Demain: --°C (Modèle) | --°C (API)")
        self.temp_demain_label.setObjectName("tempLabel")
        weather_layout.addWidget(self.temp_demain_label)

        self.prob_pluie_demain_label = QLabel("Probabilité de pluie demain : --%")
        self.prob_pluie_demain_label.setObjectName("probLabel")
        weather_layout.addWidget(self.prob_pluie_demain_label)

        self.wind_speed_demain_label = QLabel("Vent demain : -- m/s")
        self.wind_speed_demain_label.setObjectName("infoLabel")
        weather_layout.addWidget(self.wind_speed_demain_label)

        # Remove humidity and pressure for "demain" as per screenshot
        # self.humidity_demain_label = QLabel("Humidité Demain: --%")
        # self.humidity_demain_label.setObjectName("infoLabel")
        # weather_layout.addWidget(self.humidity_demain_label)

        # self.pressure_demain_label = QLabel("Pression Demain: -- hPa")
        # self.pressure_demain_label.setObjectName("infoLabel")
        # weather_layout.addWidget(self.pressure_demain_label)

        weather_layout.addSpacing(15)
        # Add a light gray separator as seen in the screenshot
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Plain) # Use Plain for a flat line
        separator.setStyleSheet("color: #e0e0e0; border-top: 1px solid #e0e0e0;") # Light gray line
        weather_layout.addWidget(separator)
        weather_layout.addSpacing(15)

        # Après-demain
        self.temp_apres_demain_label = QLabel("Temp. Max après demain : --°C (API)") # Removed "Modèle" for after tomorrow
        self.temp_apres_demain_label.setObjectName("tempLabel")
        weather_layout.addWidget(self.temp_apres_demain_label)

        self.prob_pluie_apres_demain_label = QLabel("Probabilité de pluie après demain : --%")
        self.prob_pluie_apres_demain_label.setObjectName("probLabel")
        weather_layout.addWidget(self.prob_pluie_apres_demain_label)

        self.wind_speed_apres_demain_label = QLabel("Vent après demain : -- m/s")
        self.wind_speed_apres_demain_label.setObjectName("infoLabel")
        weather_layout.addWidget(self.wind_speed_apres_demain_label)

        # Remove humidity and pressure for "apres-demain" as per screenshot
        # self.humidity_apres_demain_label = QLabel("Humidité Après-Demain: --%")
        # self.humidity_apres_demain_label.setObjectName("infoLabel")
        # weather_layout.addWidget(self.humidity_apres_demain_label)

        # self.pressure_apres_demain_label = QLabel("Pression Après-Demain: -- hPa")
        # self.pressure_apres_demain_label.setObjectName("infoLabel")
        # weather_layout.addWidget(self.pressure_apres_demain_label)


        self.scroll_content_layout.addWidget(self.weather_info_frame)
        self.scroll_content_layout.addStretch(1) # Push content to top

        self.done_label = QLabel("Terminé")
        self.done_label.setAlignment(Qt.AlignCenter)
        self.done_label.setStyleSheet("color: #28a745; font-weight: bold; font-size: 16px;")
        self.scroll_content_layout.addWidget(self.done_label)
        self.done_label.hide() # Initially hidden

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
        # Ensure consistent format with the screenshot, "Jeu. 10 juill."
        # This requires manually mapping month and weekday names for French
        jours_semaine = ["Dim.", "Lun.", "Mar.", "Mer.", "Jeu.", "Ven.", "Sam."]
        mois = [
            "janv.", "févr.", "mars", "avril", "mai", "juin",
            "juill.", "août", "sept.", "oct.", "nov.", "déc."
        ]

        jour_semaine_abbr = jours_semaine[current_datetime.weekday()]
        nom_mois_abbr = mois[current_datetime.month - 1]

        # Example: Jeu. 10 juill.
        formatted_date = f"{jour_semaine_abbr}. {current_datetime.day} {nom_mois_abbr}."
        formatted_time = current_datetime.strftime("%H:%M") # No seconds for closer match

        self.date_time_label.setText(f"{formatted_time} - {formatted_date}")
        self.date_time_label.setAlignment(Qt.AlignRight) # Ensure right alignment

    def clear_weather_display(self):
        self.city_display_label.setText("Météo pour (Ville)") # Reset to initial placeholder
        self.temp_demain_label.setText("Temp. Max Demain: --°C (Modèle) | --°C (API)")
        self.prob_pluie_demain_label.setText("Probabilité de pluie demain : --%")
        # self.humidity_demain_label.setText("Humidité Demain: --%") # Removed
        # self.pressure_demain_label.setText("Pression Demain: -- hPa") # Removed
        self.wind_speed_demain_label.setText("Vent demain : -- m/s")

        self.temp_apres_demain_label.setText("Temp. Max après demain : --°C (API)") # Removed model part
        self.prob_pluie_apres_demain_label.setText("Probabilité de pluie après demain : --%")
        # self.humidity_apres_demain_label.setText("Humidité Après-Demain: --%") # Removed
        # self.pressure_apres_demain_label.setText("Pression Après-Demain: -- hPa") # Removed
        self.wind_speed_apres_demain_label.setText("Vent après demain : -- m/s")

        # Hide status and done labels initially
        self.status_label.hide()
        self.done_label.hide()

        # Reset the weather icon
        self.set_weather_icon_display(None, self.weather_icon_label)

    def get_icon_pixmap(self, icon_filename, size=64):
        """
        Charge une QPixmap à partir d'un fichier icône, gère les erreurs et le redimensionnement.
        """
        icon_path = os.path.join(ICONS_DIR, icon_filename)
        # print(f"Tentative de chargement de l'icône: {icon_path}") # Debugging

        pixmap = QPixmap()
        if os.path.exists(icon_path) and pixmap.load(icon_path):
            # print(f"Icône chargée avec succès: {icon_filename}") # Debugging
            return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            # print(f"Erreur: Fichier icône non trouvé ou ne peut être chargé: {icon_path}") # Debugging
            return QPixmap() # Retourne une QPixmap nulle

    def set_weather_icon_display(self, prob_pluie, target_label):
        """
        Définit l'icône appropriée sur le QLabel cible en fonction de la probabilité de pluie.
        """
        # Clear any existing movie/pixmap
        if target_label.movie():
            target_label.movie().stop()
            target_label.setMovie(None)
        target_label.clear()

        # Handle loading state first
        if prob_pluie == 'loading':
            loading_path = os.path.join(ICONS_DIR, 'loading.gif')
            if os.path.exists(loading_path):
                movie = QMovie(loading_path)
                if movie.isValid():
                    movie.setScaledSize(target_label.size())
                    target_label.setMovie(movie)
                    movie.start()
                    self.status_label.setText("Status...") # Show "Status..." during loading
                    self.status_label.show()
                else:
                    target_label.setText("...")
                    self.status_label.setText("Chargement...")
                    self.status_label.show()
            else:
                target_label.setText("...")
                self.status_label.setText("Chargement...")
                self.status_label.show()
            return

        # Hide status label once loading is done
        self.status_label.hide()

        prob_int = -1
        if isinstance(prob_pluie, str) and prob_pluie.endswith('%'):
            try:
                prob_int = int(prob_pluie.replace('%', ''))
            except ValueError:
                pass # prob_int remains -1

        icon_filename = "default.png" # Default icon, e.g., question mark or generic weather

        # Logic for choosing icon based on probability
        if prob_int >= 70:
            icon_filename = "heavy_rain.png" # You'll need this icon
        elif prob_int >= 40:
            icon_filename = "rain.png" # You'll need this icon
        elif prob_int >= 0: # 0-39% chance of rain, implies sun or partial clouds
            icon_filename = "sun.png" # You'll need this icon

        # Attempt to load the pixmap at the target label's fixed size
        final_pixmap = self.get_icon_pixmap(icon_filename, size=target_label.width())

        if not final_pixmap.isNull():
            target_label.setPixmap(final_pixmap)
        else:
            # Fallback to a generic default if specific icon isn't found
            default_fallback_pixmap = self.get_icon_pixmap("default.png", size=target_label.width())
            if not default_fallback_pixmap.isNull():
                target_label.setPixmap(default_fallback_pixmap)
            else:
                target_label.setText("?") # Show a question mark if no icon can be loaded

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
        self.set_weather_icon_display('loading', self.weather_icon_label) # Show loading GIF
        self.done_label.hide() # Hide 'Terminé' during search

        # Simulate API call with a delay if needed for testing loading state
        # QTimer.singleShot(1000, lambda: self._fetch_and_display_weather(city_name))
        # For actual use, call directly:
        self._fetch_and_display_weather(city_name)

    def _fetch_and_display_weather(self, city_name):
        api_data = fetch_weather_data(city_name)

        if api_data and api_data["temp_max_demain"] is not None:
            temp_api_demain = api_data.get("temp_max_demain")
            prob_pluie_demain = api_data.get("prob_pluie_demain")
            humidity_demain = api_data.get("humidity_demain")
            pressure_demain = api_data.get("pressure_demain")
            wind_speed_demain = api_data.get("wind_speed_demain")

            temp_api_apres_demain = api_data.get("temp_max_apres_demain")
            prob_pluie_apres_demain = api_data.get("prob_pluie_apres_demain")
            # humidity_apres_demain = api_data.get("humidity_apres_demain") # Not used in display per screenshot
            # pressure_apres_demain = api_data.get("pressure_apres_demain") # Not used in display per screenshot
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
            temp_modele_demain_display = temp_api_demain # Default to API if model fails
            if temp_modele_demain is not None:
                temp_modele_demain_display = temp_modele_demain
                model_status_text = "Modèle"

            self.city_display_label.setText(f"Météo pour {city_name}")

            self.temp_demain_label.setText(
                f"Temp. Max Demain: {temp_modele_demain_display}°C ({model_status_text}) | {temp_api_demain}°C (API)"
            )

            self.prob_pluie_demain_label.setText(f"Probabilité de pluie demain : {prob_pluie_demain if prob_pluie_demain is not None else '--'}%")
            self.wind_speed_demain_label.setText(f"Vent demain : {wind_speed_demain if wind_speed_demain is not None else '--'} m/s")

            self.temp_apres_demain_label.setText(f"Temp. Max après demain : {temp_api_apres_demain if temp_api_apres_demain is not None else '--'}°C (API)") # Explicitly API for after tomorrow
            self.prob_pluie_apres_demain_label.setText(f"Probabilité de pluie après demain : {prob_pluie_apres_demain if prob_pluie_apres_demain is not None else '--'}%")
            self.wind_speed_apres_demain_label.setText(f"Vent après demain : {wind_speed_apres_demain if wind_speed_apres_demain is not None else '--'} m/s")

            # Appliquer les icônes
            self.set_weather_icon_display(f"{prob_pluie_demain}%" if prob_pluie_demain is not None else 'N/A', self.weather_icon_label)
            self.done_label.show() # Show 'Terminé' when data is successfully loaded

            # Save observations for tomorrow
            self.save_observation(
                city_name, date_demain, temp_modele_demain_display, temp_api_demain,
                humidity_demain, pressure_demain, wind_speed_demain
            )

            # Save observations for after tomorrow (using API data for model temp)
            if temp_api_apres_demain is not None:
                self.save_observation(
                    city_name, date_apres_demain, temp_api_apres_demain, temp_api_apres_demain,
                    api_data.get("humidity_apres_demain"), api_data.get("pressure_apres_demain"), api_data.get("wind_speed_apres_demain")
                )

        else:
            self.city_display_label.setText(f"Météo pour {city_name} (Données non trouvées)")
            self.clear_weather_display() # Clears all labels and hides status/done
            QMessageBox.information(self, "Données Météo", f"Impossible de récupérer les données météo pour {city_name}. Vérifiez le nom de la ville ou votre clé API.")
            self.set_weather_icon_display(None, self.weather_icon_label) # Reset icon to default/blank
            self.status_label.hide() # Ensure status is hidden
            self.done_label.hide() # Ensure done is hidden


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec_())
