# Incentives Report

App de Streamlit para analizar el CSV de incentivos DSL 2026.

## Que muestra

- Ranking de jugadores con mayores ganancias.
- Items que mas aportan al total.
- Desglose por jugador: conteo, tarifa y monto por item.
- Filtro por team.
- Descarga del detalle filtrado en CSV.

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar en GitHub y Streamlit

1. Crea un repositorio nuevo en GitHub.
2. Sube estos archivos al repo:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `data/incentives.csv`
3. Entra a [Streamlit Community Cloud](https://streamlit.io/cloud).
4. Conecta tu cuenta de GitHub.
5. Elige el repositorio, branch principal y `app.py` como archivo de entrada.
6. Presiona **Deploy**. Streamlit generara un link publico.

## Nota de privacidad

Si el CSV tiene informacion sensible, no lo publiques dentro del repositorio. En ese caso, guarda el CSV en una URL privada o en `st.secrets` y configura la variable `INCENTIVES_CSV_URL` para que la app lea desde ahi.
