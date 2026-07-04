import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Las 500 Mejores Películas Según Letterboxd",
    page_icon="🎬",
    layout="wide"
)

st.title("Página Interactiva sobre las 500 Mejores Películas Según Letterboxd")

# -----------------------------------------------------------------------------
# 1. CARGA DE DATOS
# -----------------------------------------------------------------------------
@st.cache_data
def cargar_datos():
    # Intenta leer del directorio actual para mayor flexibilidad en Streamlit
    try:
        return pd.read_csv("top500.csv")
    except FileNotFoundError:
        return pd.read_csv("/content/top500.csv")

df_top500 = cargar_datos()

# Creación de pestañas para organizar la app de forma profesional
tab1, tab2, tab3 = st.tabs(["Dashboard Estadístico", "Explorador de Películas", "Recomiéndame Una Película"])

# -----------------------------------------------------------------------------
# TAB 1: ESTADÍSTICAS Y GRÁFICOS
# -----------------------------------------------------------------------------
with tab1:
    st.header("Análisis de Datos del Top 500")
    
    # Fila 1: Mapa y Línea de Tiempo
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Cantidad de Películas por País")
        country_count = df_top500["country"].value_counts().reset_index()
        country_count.columns = ["country", "Cantidad de películas"]

        fig_map = px.choropleth(
            country_count,
            locations="country",
            locationmode="country names",
            color="Cantidad de películas",
            hover_name="country",
            color_continuous_scale="Greens"
        )
        fig_map.update_layout(height=400, margin={"r":0,"t":30,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)

    with col2:
        st.subheader("Películas por Año de Estreno")
        year_counts = df_top500['year'].value_counts().sort_index().reset_index()
        year_counts.columns = ['Año', 'Cantidad de Películas']

        fig_line = px.line(
            year_counts, x='Año', y='Cantidad de Películas',
            markers=True, labels={'Año': 'Año de Estreno', 'Cantidad de Películas': 'Cantidad'}
        )
        fig_line.update_layout(height=400)
        st.plotly_chart(fig_line, use_container_width=True)

    # Fila 2: Directores y Géneros (Seaborn / Matplotlib)
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Top 10 Directores más Comunes")
        director_cols = [col for col in df_top500.columns if 'director/' in col]
        all_directors = df_top500[director_cols].stack().dropna().tolist()
        director_counts = pd.Series(all_directors).value_counts().reset_index()
        director_counts.columns = ['Director', 'Cantidad de Películas']
        
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x='Cantidad de Películas', y='Director', data=director_counts.head(10), palette='viridis', ax=ax)
        plt.tight_layout()
        st.pyplot(fig)

    with col4:
        st.subheader("Top 10 Géneros más Comunes")
        genre_cols = [col for col in df_top500.columns if 'genres/' in col]
        df_top500['genres_combined'] = df_top500[genre_cols].apply(lambda row: ', '.join(row.dropna().astype(str)), axis=1)
        all_genres = df_top500['genres_combined'].str.split(', ').explode().str.strip().tolist()
        all_genres = [genre for genre in all_genres if genre]
        genre_counts = pd.Series(all_genres).value_counts().reset_index()
        genre_counts.columns = ['Género', 'Cantidad de Películas']
        
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x='Cantidad de Películas', y='Género', data=genre_counts.head(10), palette='magma', ax=ax)
        plt.tight_layout()
        st.pyplot(fig)

    # Fila 3: Top 20 Películas por número de vistas
    st.subheader("Top 20 Películas por Número de Personas que las Han Visto")
    top_20_movies = df_top500.sort_values(by='ratingsCount', ascending=False).head(20)
    fig_bar = px.bar(
        top_20_movies, x='title', y='ratingsCount',
        labels={'title': 'Título de la Película', 'ratingsCount': 'Votos / Audiencia'},
        hover_data={'averageRating': True, 'year': True, 'country': True}
    )
    fig_bar.update_xaxes(tickangle=45)
    st.plotly_chart(fig_bar, use_container_width=True)


# -----------------------------------------------------------------------------
# TAB 2: BUSCADOR DE PELÍCULAS
# -----------------------------------------------------------------------------
with tab2:
    st.header("Buscador por Filtros")
    
    opcion_busqueda = st.radio("Buscar por:", ["País", "Género"])
    
    if opcion_busqueda == "País":
        paises_disponibles = sorted(df_top500["country"].dropna().unique())
        pais_seleccionado = st.selectbox("Selecciona un país:", paises_disponibles)
        resultado_busqueda = df_top500[df_top500["country"] == pais_seleccionado]
    else:
        generos_lista = ["Adventure", "Drama", "Fantasy", "Music", "Romance", "Thriller", "War", "Western"]
        genero_seleccionado = st.selectbox("Selecciona un género:", generos_lista)
        resultado_busqueda = df_top500[df_top500['genres_combined'].str.contains(genero_seleccionado, case=False, na=False)]

    # Mostrar películas encontradas en un formato amigable de tarjetas
    resultado_busqueda = resultado_busqueda.sort_values(by='averageRating', ascending=False)
    
    if resultado_busqueda.empty:
        st.warning("No se encontraron películas para los criterios seleccionados.")
    else:
        st.success(f"Se encontraron {len(resultado_busqueda)} películas.")
        for index, row in resultado_busqueda.iterrows():
            with st.container():
                c1, c2 = st.columns([1, 4])
                with c1:
                    poster = row["posterUrl"] if "posterUrl" in row and pd.notna(row["posterUrl"]) else None
                    if poster:
                        st.image(poster, width=120)
                    else:
                        st.image("https://via.placeholder.com/120x180?text=No+Poster", width=120)
                with c2:
                    st.subheader(f"{row['title']} ({int(row['year'])})")
                    director = row["director/0"] if "director/0" in row and pd.notna(row["director/0"]) else "N/A"
                    st.write(f"**Director:** {director}")
                    st.write(f"**Calificación Promedio:** ⭐ {row['averageRating']}")
                    if 'genres_combined' in row:
                        st.write(f"**Géneros:** {row['genres_combined']}")
                st.markdown("---")


# -----------------------------------------------------------------------------
# TAB 3: QUIZ RECOMENDADOR
# -----------------------------------------------------------------------------
def cargar_y_limpiar_datos(df_source):
    df = df_source.copy()
    df = df.rename(columns={
        'title': 'título', 'year': 'año', 'country': 'país o región', 'averageRating': 'rating de Letterboxd'
    })
    df = df.rename(columns={f'director/{i}': f'director{i}' for i in range(3) if f'director/{i}' in df.columns})
    df = df.rename(columns={f'genres/{i}': f'género{i}' for i in range(8) if f'genres/{i}' in df.columns})
    
    if 'sinopsis' not in df.columns: df['sinopsis'] = ''
    if 'duración (minutos)' not in df.columns: df['duración (minutos)'] = 120
    if 'idioma' not in df.columns: df['idioma'] = 'inglés'

    columnas_str = ['título', 'sinopsis', 'idioma', 'país o región'] + [f'director{i}' for i in range(3) if f'director{i}' in df.columns]
    for col in columnas_str:
        if col in df.columns: df[col] = df[col].astype(str).str.strip()

    for i in range(8):
        col_gen = f'género{i}'
        if col_gen in df.columns: df[col_gen] = df[col_gen].astype(str).str.strip().str.capitalize()
    return df

def filtrar_y_puntuar(df, respuestas):
    df_filtrado = df.copy()

    # Evitar géneros
    if respuestas['evitar'] and respuestas['evitar'] != 'Ninguno':
        for i in range(8):
            if f'género{i}' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado[f'género{i}'] != respuestas['evitar']]

    df_filtrado['score'] = 0.0

    # Coincidencia de Género
    if respuestas['genero'] != 'Ninguno':
        gen_mask = pd.Series(False, index=df_filtrado.index)
        for i in range(8):
            if f'género{i}' in df_filtrado.columns:
                gen_mask = gen_mask | (df_filtrado[f'género{i}'] == respuestas['genero'])
        df_filtrado.loc[gen_mask, 'score'] += 3.0

    # Experiencia Emocional
    dic_palabras_clave = {
        'emocionarme': ['llorar', 'amor', 'drama', 'emoción', 'conmovedor', 'familia', 'triste', 'vida'],
        'reflexionar': ['filosofía', 'mente', 'pensar', 'existencial', 'sociedad', 'realidad', 'humano', 'moral'],
        'suspenso': ['misterio', 'crimen', 'asesinato', 'tensión', 'peligro', 'secreto', 'investigación', 'terror'],
        'reír': ['comedia', 'divertido', 'humor', 'chiste', 'risa', 'sátira', 'parodia'],
        'sorprenderme': ['giro', 'inesperado', 'secreto', 'magia', 'ciencia ficción', 'fantasía', 'viaje', 'descubrir']
    }
    exp = respuestas['experiencia'].lower()
    if exp in dic_palabras_clave:
        regex_pattern = '|'.join(dic_palabras_clave[exp])
        sinopsis_match = df_filtrado['sinopsis'].str.contains(regex_pattern, case=False, na=False)
        df_filtrado.loc[sinopsis_match, 'score'] += 2.0

    # Rating
    if 'rating de Letterboxd' in df_filtrado.columns:
        df_filtrado['score'] += (df_filtrado['rating de Letterboxd'].fillna(0) / 5.0) * 2.0

    # Duración
    dur = respuestas['duracion']
    if dur == 'Menos de 90 minutos': df_filtrado.loc[df_filtrado['duración (minutos)'] < 90, 'score'] += 1.0
    elif dur == '90–120 minutos': df_filtrado.loc[(df_filtrado['duración (minutos)'] >= 90) & (df_filtrado['duración (minutos)'] <= 120), 'score'] += 1.0
    elif dur == '120–150 minutos': df_filtrado.loc[(df_filtrado['duración (minutos)'] > 120) & (df_filtrado['duración (minutos)'] <= 150), 'score'] += 1.0
    elif dur == 'Más de 150 minutos': df_filtrado.loc[df_filtrado['duración (minutos)'] > 150, 'score'] += 1.0

    # Época
    ep = respuestas['epoca']
    if ep == 'Antes de 1970': df_filtrado.loc[df_filtrado['año'] < 1970, 'score'] += 1.0
    elif ep == '1970–1989': df_filtrado.loc[(df_filtrado['año'] >= 1970) & (df_filtrado['año'] <= 1989), 'score'] += 1.0
    elif ep == '1990–2009': df_filtrado.loc[(df_filtrado['año'] >= 1990) & (df_filtrado['año'] <= 2009), 'score'] += 1.0
    elif ep == '2010+': df_filtrado.loc[df_filtrado['año'] >= 2010, 'score'] += 1.0

    # Rating Mínimo
    rat = respuestas['rating']
    if rat == '3.5+': df_filtrado = df_filtrado[df_filtrado['rating de Letterboxd'] >= 3.5]
    elif rat == '4.0+': df_filtrado = df_filtrado[df_filtrado['rating de Letterboxd'] >= 4.0]
    elif rat == '4.3+': df_filtrado = df_filtrado[df_filtrado['rating de Letterboxd'] >= 4.3]
    elif rat == 'Top rated (4.5+)': df_filtrado = df_filtrado[df_filtrado['rating de Letterboxd'] >= 4.5]

    # Región
    reg = respuestas['region'].lower()
    if reg != 'cualquiera':
        mapa_regiones = {
            'usa/canadá': ['estados unidos', 'canadá', 'usa', 'united states', 'canada'],
            'europa': ['europa', 'francia', 'españa', 'reino unido', 'italia', 'alemania'],
            'asia': ['asia', 'japón', 'corea', 'china', 'india'],
            'latinoamérica': ['latinoamérica', 'argentina', 'méxico', 'brasil', 'chile', 'colombia']
        }
        if reg in mapa_regiones:
            reg_mask = df_filtrado['país o región'].str.lower().isin(mapa_regiones[reg])
            df_filtrado.loc[reg_mask, 'score'] += 1.0

    # Director
    if respuestas['director']:
        dir_mask = pd.Series(False, index=df_filtrado.index)
        for i in range(3):
            if f'director{i}' in df_filtrado.columns:
                dir_mask = dir_mask | (df_filtrado[f'director{i}'].str.lower() == respuestas['director'].lower().strip())
        df_filtrado.loc[dir_mask, 'score'] += 1.5

    df_filtrado = df_filtrado.sort_values(by=['score', 'rating de Letterboxd'], ascending=[False, False])
    return df_filtrado

with tab3:
    st.header("Cuestionario de Recomendación Personalizada")
    df_quiz_data = cargar_y_limpiar_datos(df_top500)
    
    # Formulario del Quiz
    with st.form("quiz_form"):
        c1, c2 = st.columns(2)
        with c1:
            g_pref = st.selectbox("1. ¿Qué género te gustaría ver hoy?", ["Ninguno", "Drama", "Comedy", "Action", "Thriller", "Horror", "Romance", "Sci-fi", "Animation", "Fantasy", "Adventure"])
            dur_opt = st.selectbox("2. ¿Qué duración prefieres?", ["Me da igual", "Menos de 90 minutos", "90–120 minutos", "120–150 minutos", "Más de 150 minutos"])
            ep_opt = st.selectbox("3. ¿De qué época prefieres la película?", ["No importa", "Antes de 1970", "1970–1989", "1990–2009", "2010+"])
            rat_opt = st.selectbox("4. ¿Qué calificación mínima buscas?", ["Me da igual", "3.5+", "4.0+", "4.3+", "Top rated (4.5+)"])
            region_opt = st.selectbox("5. ¿De qué región te gustaría ver la película?", ["Cualquiera", "USA/Canadá", "Europa", "Asia", "Latinoamérica"])
        with c2:
            id_opt = st.selectbox("6. ¿Qué prefieres respecto al idioma?", ["Cualquier idioma", "Español", "Español/Inglés", "Descubrir otros"])
            exp_opt = st.selectbox("7. ¿Qué tipo de experiencia buscas?", ["Indiferente", "Emocionarme", "Reflexionar", "Suspenso", "Reír", "Sorprenderme"])
            evitar_opt = st.selectbox("8. ¿Quieres evitar algún género?", ["Ninguno", "Horror", "Comedy", "Drama", "Action"])
            dir_opt = st.text_input("9. ¿Hay algún director que te guste especialmente? (Opcional)")
            n_recom = st.slider("10. ¿Cuántas recomendaciones deseas?", 1, 5, 3)
            
        enviado = st.form_submit_button("Obtener Recomendaciones")

    if enviado:
        respuestas = {
            'genero': g_pref, 'duracion': dur_opt, 'epoca': ep_opt, 'rating': rat_opt,
            'region': region_opt, 'idioma': id_opt, 'experiencia': exp_opt, 'evitar': evitar_opt,
            'director': dir_opt, 'cantidad': n_recom
        }
        
        resultados = filtrar_y_puntuar(df_quiz_data, respuestas)
        n_mostrar = min(len(resultados), respuestas['cantidad'])
        
        if n_mostrar == 0:
            st.error("No se encontraron películas que coincidan con tus filtros estrictos. ¡Prueba relajando tus criterios!")
        else:
            st.success(f"Aquí tienes tus {n_mostrar} mejores opciones recomendadas:")
            for idx in range(n_mostrar):
                peli = resultados.iloc[idx]
                
                # Juntar géneros y directores válidos
                generos = [str(peli[f'género{i}']) for i in range(8) if f'género{i}' in peli and pd.notna(peli[f'género{i}']) and str(peli[f'género{i}']).lower() != 'nan' and str(peli[f'género{i}']) != '']
                directores = [str(peli[f'director{i}']) for i in range(3) if f'director{i}' in peli and pd.notna(peli[f'director{i}']) and str(peli[f'director{i}']).lower() != 'nan' and str(peli[f'director{i}']) != '']
                
                # Motivo simplificado
                por_que = f"Esta obra maestra tiene una alta afinidad con tu búsqueda debido a sus excelentes calificaciones ({peli['rating de Letterboxd']}) y el balance de tus preferencias de género y época."
                
                with st.chat_message("user", avatar="🎬"):
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        poster_url = peli["posterUrl"] if "posterUrl" in peli.index and pd.notna(peli["posterUrl"]) else None
                        if poster_url: st.image(poster_url, width=110)
                        else: st.image("https://via.placeholder.com/110x160?text=No+Poster", width=110)
                    with c2:
                        st.subheader(f"{peli['título']} ({int(peli['año'])})")
                        st.write(f"**Director(es):** {', '.join(directores)}")
                        st.write(f"**Calificación:** ⭐ {peli['rating de Letterboxd']} | **País:** {peli['país o región']} | **Duración:** {int(peli['duración (minutos)'])} min")
                        st.write(f"**Géneros:** {', '.join(generos)}")
                        st.info(f"💡 **Por qué te la recomendamos:** {por_que}")
