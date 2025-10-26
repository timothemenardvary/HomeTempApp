import streamlit as st
import pandas as pd
import plotly.express as px
import datetime 

link=r"https://docs.google.com/spreadsheets/d/1rOOcih0w9ggjRePOjEhC5EIhKwZVVUY7HnwgZGoRftc/edit?usp=sharing"

# --- CONFIG ---
st.set_page_config(page_title="Visualisation Températures", layout="wide")

# --- SIDEBAR ---
st.sidebar.header("Configuration")
sheet_url = st.sidebar.text_input(
    "Lien Google Sheet",
    link
)

# --- LOAD DATA ---

def load_data(sheet_url):
    # Conversion du lien Google Sheet en CSV
    if "/edit" in sheet_url:
        csv_url = sheet_url.split("/edit")[0] + "/export?format=csv"
    else:
        csv_url = sheet_url

    df = pd.read_csv(csv_url, decimal=",")
    df.columns = [c.strip().lower() for c in df.columns]  # nettoyage colonnes
    # Liste des colonnes de température
    temp_cols = [c for c in df.columns if c != "horodateur"]

    # Normaliser les décimales : remplacer ',' par '.' et convertir en float
    for col in temp_cols:
        df[col] = df[col].astype(str).str.replace(',', '.')
        df[col] = pd.to_numeric(df[col], errors='coerce')


    # Trouver automatiquement la colonne de date
    datetime_col = None
    for candidate in df.columns:
        if "date" in candidate or "time" in candidate or "heure" in candidate or "horodateur" in candidate:
            datetime_col = candidate
            break

    if datetime_col is None:
        st.error("❌ Impossible de trouver une colonne de type 'date' ou 'heure' dans le fichier.")
        st.write("Colonnes détectées :", df.columns.tolist())
        return pd.DataFrame()

    # Conversion en datetime
    df["datetime"] = pd.to_datetime(df[datetime_col], format="%d/%m/%Y %H:%M:%S", errors="coerce")

    df.drop(columns=["horodateur"], inplace=True)
    df = df.dropna(subset=['datetime'])
    return df


df = load_data(sheet_url)

# --- MAIN ---
st.title("🌡️ Visualisation des Températures")
st.write("Visualisation interactive des données issues de ton Google Sheet.")

if df.empty:
    st.warning("Aucune donnée chargée. Vérifie ton lien Google Sheet.")
else:
    st.subheader("Aperçu des données")
    # Trier par datetime décroissant
    df_sorted = df.sort_values(by="datetime", ascending=False)

    # Afficher le tableau scrollable
    st.dataframe(df_sorted, use_container_width=True, height=200)


    # Choix des capteurs
    sensors = [col for col in df.columns if col != "datetime"]
    selected_sensors = st.multiselect(
        "Choisis les capteurs à afficher :", sensors, default=sensors
    )

    # Graphique
    if selected_sensors:
     # --- CURSEUR DE ZOOM SUR LES DATES ---
        min_date = df["datetime"].min().to_pydatetime()
        max_date = df["datetime"].max().to_pydatetime()
        start_date, end_date = st.slider(
            "Sélectionne la plage de dates",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="DD/MM/YYYY HH:mm"
        )

        df_filtered = df_sorted[
            (df_sorted["datetime"] >= start_date) & (df_sorted["datetime"] <= end_date)
        ].copy()

        # Conversion des colonnes en numérique
        for col in selected_sensors:
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors="coerce")

        # --- GRAPHIQUE ---
        fig = px.line(
            df_filtered,
            x="datetime",
            y=selected_sensors,
            title="Évolution des Températures",
            labels={"value": "Température (°C)", "datetime": "Date/Heure"}
        )

        # Personnaliser la courbe "temp netatmo out"
        if "temp netatmo out" in selected_sensors:
            for trace in fig.data:
                if trace.name.lower() == "temp netatmo out":
                    trace.line.color = "gray"
                    trace.line.dash = "dash"  # haché

        if "temp netatmo hub" in selected_sensors:
            for trace in fig.data:
                if trace.name.lower() == "temp netatmo hub":
                    trace.line.color = "#ab1a0f"

        if "temp homepod bureau" in selected_sensors:
            for trace in fig.data:
                if trace.name.lower() == "temp homepod bureau":
                    trace.line.color = "#e1807a"

        if "temp homepod salon" in selected_sensors:
            for trace in fig.data:
                if trace.name.lower() == "temp homepod salon":
                    trace.line.color = "#7979df"
        
        if "temp homepod cuisine" in selected_sensors:
            for trace in fig.data:
                if trace.name.lower() == "temp homepod salon":
                    trace.line.color = "#062951"

        st.plotly_chart(fig, use_container_width=True)

        # --- STATS SIMPLES ---
        st.subheader("Statistiques des capteurs sur la période sélectionnée")
        stats = df_filtered[selected_sensors].agg(["min", "mean", "max"])
        st.table(stats)
    else:
        st.info("Sélectionne au moins une série à afficher.")
