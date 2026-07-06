import streamlit as st
import pandas as pd
import io

# Configuración inicial de la página (debe ser la primera instrucción de Streamlit)
st.set_page_config(
    page_title="Analizador de Apuestas",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def procesar_archivo(archivo):
    """
    Lee el archivo subido (CSV o Excel) y retorna un DataFrame de Pandas.
    """
    try:
        if archivo.name.endswith('.csv'):
            # Intentamos leer con separador de coma, si falla probamos con punto y coma
            try:
                df = pd.read_csv(archivo)
            except:
                df = pd.read_csv(archivo, sep=';')
        elif archivo.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(archivo)
        else:
            st.error("Formato de archivo no soportado.")
            return None
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return None

def filtrar_mejores_opciones(df, col_cuota="Cuota", col_probabilidad="Probabilidad"):
    """
    Filtra las apuestas buscando 'Value' (Valor Esperado Positivo).
    Fórmula clásica: (Cuota * Probabilidad / 100) > 1
    
    Si las columnas por defecto no existen, se solicita al usuario configurarlas.
    """
    # Verificamos si las columnas esperadas existen en el DataFrame
    columnas_df = df.columns.tolist()
    
    if col_cuota in columnas_df and col_probabilidad in columnas_df:
        # Limpieza de datos (por si vienen como texto con símbolos)
        df_limpio = df.copy()
        df_limpio[col_cuota] = pd.to_numeric(df_limpio[col_cuota].astype(str).str.replace(',', '.'), errors='coerce')
        df_limpio[col_probabilidad] = pd.to_numeric(df_limpio[col_probabilidad].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce')
        
        # Eliminamos filas con valores nulos en las columnas clave
        df_limpio = df_limpio.dropna(subset=[col_cuota, col_probabilidad])
        
        # Calculamos el Valor Esperado (EV) y filtramos donde EV > 1 (o EV > 0% de retorno)
        # Ajustaremos el filtro para buscar un margen de valor superior al 5% (EV > 1.05)
        df_limpio['Valor_Esperado'] = (df_limpio[col_cuota] * (df_limpio[col_probabilidad] / 100))
        mejores_opciones = df_limpio[df_limpio['Valor_Esperado'] >= 1.05].copy()
        
        # Ordenamos por el mayor valor esperado
        mejores_opciones = mejores_opciones.sort_values(by='Valor_Esperado', ascending=False)
        return mejores_opciones
    else:
        # Si no encuentra las columnas, devuelve el DataFrame vacío e informa
        return pd.DataFrame()

def main():
    # 1. Título principal de la aplicación
    st.title("⚽ Analizador de Apuestas Deportivas")
    st.markdown("Sube tus proyecciones estadísticas y encuentra automáticamente las apuestas con mayor valor.")
    st.divider()

    # 2. Zona para subir el archivo
    st.subheader("📁 Carga de Datos")
    archivo_subido = st.file_uploader("Selecciona un archivo CSV o Excel", type=['csv', 'xlsx', 'xls'])

    if archivo_subido is not None:
        # Cargamos los datos
        df = procesar_archivo(archivo_subido)
        
        if df is not None:
            # 3. Tabla interactiva general
            st.subheader("📊 Datos Completos del Análisis")
            st.dataframe(df, use_container_width=True)
            
            st.divider()
            
            # 4. Sección Destacada: Las Mejores Opciones del Día
            st.subheader("🌟 Las Mejores Opciones del Día (Apuestas de Valor)")
            
            # Opciones de configuración de columnas dinámicas en caso de nombres distintos
            with st.expander("⚙️ Configurar columnas de filtrado (Opcional)"):
                col1, col2 = st.columns(2)
                with col1:
                    col_cuota_sel = st.selectbox("Selecciona la columna de Cuota/Odds", df.columns, index=0)
                with col2:
                    col_prob_sel = st.selectbox("Selecciona la columna de Probabilidad (%)", df.columns, index=min(1, len(df.columns)-1))
            
            # 5. Lógica para filtrar las apuestas de forma automática
            mejores_df = filtrar_mejores_opciones(df, col_cuota=col_cuota_sel, col_probabilidad=col_prob_sel)
            
            if not mejores_df.empty:
                st.success(f"¡Se han encontrado {len(mejores_df)} apuestas de alto valor!")
                # Mostramos la tabla destacada
                st.dataframe(mejores_df, use_container_width=True)
                
                # Opción para descargar los resultados filtrados
                csv_export = mejores_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar Mejores Opciones (CSV)",
                    data=csv_export,
                    file_name='mejores_apuestas_del_dia.csv',
                    mime='text/csv',
                )
            else:
                st.info("No se encontraron apuestas que cumplan con los criterios de valor estricto (EV > 5%), o las columnas seleccionadas no contienen datos numéricos válidos.")

if __name__ == "__main__":
    main()
