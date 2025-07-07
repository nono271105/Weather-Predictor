# Prédicteur de Météo Locale ⛅️
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Ce projet est une application de bureau en Python permettant de prédire la météo locale (température maximale, probabilité de pluie, humidité, pression, vent) pour une ville donnée, en combinant les données de l'API OpenWeatherMap et un modèle de machine learning entraîné sur vos propres observations.

## Fonctionnalités

- Interface graphique moderne avec PyQt5
- Recherche météo par ville
- Affichage des prévisions pour demain et après-demain (température, pluie, humidité, pression, vent)
- Icônes météo dynamiques
- Sauvegarde automatique des observations dans un fichier CSV
- Entraînement et utilisation d'un modèle de prédiction (RandomForest)
- Support multi-plateforme

## Structure du projet

```
.
├── app/
│   ├── main.py           # Interface graphique principale
│   ├── weather_api.py    # Récupération des données météo via API
│   └── __init__.py
├── assets/
│   └── icons/            # Icônes météo (PNG, GIF)
├── data/
│   ├── models/           # Modèles ML sauvegardés (.pkl)
│   └── observations/     # Observations météo (.csv)
├── training/
│   └── train_model.py    # Script d'entraînement du modèle
├── requirements.txt      # Dépendances Python
├── .env                  # Clé API OpenWeatherMap
└── .gitignore
```

## Installation

1. **Cloner le dépôt :**
   ```sh
   git clone <url_du_repo>
   cd weather_predictor
   ```

2. **Installer les dépendances :**
   ```sh
   pip install -r requirements.txt
   ```

3. **Configurer la clé API :**
   - Créez un fichier `.env` à la racine avec :
     ```
     OPENWEATHER_API_KEY=VOTRE_CLE_API
     ```
   - Remplacez `VOTRE_CLE_API` par votre clé personnelle obtenue sur [OpenWeatherMap](https://openweathermap.org/api).

## Utilisation

### Lancer l'application graphique

```sh
python app/main.py
```

### Entraîner le modèle de prédiction

Après avoir collecté des observations (le fichier `data/observations/temperature_observations.csv` se remplit automatiquement), lancez :

```sh
python training/train_model.py
```

Un nouveau modèle sera sauvegardé dans `data/models/`.

## Remarques

- Les observations sont ajoutées automatiquement à chaque recherche météo.
- Le modèle ML est utilisé uniquement s'il existe au moins un fichier `.pkl` dans `data/models/`.
- Les icônes météo doivent être placées dans `assets/icons/` (voir exemples fournis).

## Dépendances principales

- PyQt5
- requests
- pandas
- scikit-learn
- joblib

## Licence

Ce projet est fourni à des fins éducatives.
