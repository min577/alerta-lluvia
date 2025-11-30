import streamlit as st
import pydeck as pdk
import pandas as pd
import folium
from streamlit_folium import st_folium

# Mapbox API 키
MAPBOX_API_KEY = "pk.eyJ1IjoibTFudTMiLCJhIjoiY21pbGpmN3ZxMW83dzNjcXh6dGNkZWZhcSJ9.LQCHmf6pR46a0arkhQOJQg"

# 페이지 설정
st.set_page_config(
    page_title="Alerta Lluvia - Asunción",
    page_icon="🌧️",
    layout="wide"
)

# 제목
st.title("🌧️ Alerta Lluvia")
st.subheader("Sistema de Predicción de Inundaciones con Terreno 3D")
st.markdown("AI 기반 침수 예측 시스템 - 3D 지형 시각화")

st.divider()

# 아순시온 구역 데이터 (고도 정보 추가)
zonas = [
    {"nombre": "Centro Histórico", "lat": -25.2819, "lon": -57.6350, "vulnerabilidad": 4, "elevacion": 65},
    {"nombre": "Sajonia", "lat": -25.2700, "lon": -57.6450, "vulnerabilidad": 5, "elevacion": 45},
    {"nombre": "Recoleta", "lat": -25.2900, "lon": -57.6100, "vulnerabilidad": 2, "elevacion": 95},
    {"nombre": "Villa Morra", "lat": -25.2950, "lon": -57.5800, "vulnerabilidad": 2, "elevacion": 110},
    {"nombre": "San Lorenzo", "lat": -25.3400, "lon": -57.5100, "vulnerabilidad": 3, "elevacion": 85},
    {"nombre": "Luque", "lat": -25.2700, "lon": -57.4900, "vulnerabilidad": 3, "elevacion": 90},
    {"nombre": "Lambaré", "lat": -25.3500, "lon": -57.6100, "vulnerabilidad": 4, "elevacion": 55},
    {"nombre": "Fernando de la Mora", "lat": -25.3200, "lon": -57.5500, "vulnerabilidad": 3, "elevacion": 80},
    {"nombre": "Zeballos Cué", "lat": -25.2600, "lon": -57.5700, "vulnerabilidad": 5, "elevacion": 50},
    {"nombre": "Bañado Norte", "lat": -25.2550, "lon": -57.6300, "vulnerabilidad": 5, "elevacion": 40},
    {"nombre": "Bañado Sur", "lat": -25.3100, "lon": -57.6400, "vulnerabilidad": 5, "elevacion": 42},
    {"nombre": "Trinidad", "lat": -25.3050, "lon": -57.5650, "vulnerabilidad": 2, "elevacion": 100},
]

# 사이드바 - 입력 컨트롤
st.sidebar.header("⚙️ Parámetros de Simulación")
st.sidebar.markdown("시뮬레이션 매개변수")

precipitacion = st.sidebar.slider(
    "🌧️ Precipitación prevista (mm)",
    min_value=0,
    max_value=150,
    value=30,
    step=5,
    help="예상 강우량 (mm)"
)

duracion = st.sidebar.slider(
    "⏱️ Duración de lluvia (horas)",
    min_value=1,
    max_value=12,
    value=3,
    help="강우 지속 시간"
)

nivel_rio = st.sidebar.slider(
    "🌊 Nivel del Río Paraguay (m)",
    min_value=0.0,
    max_value=10.0,
    value=3.5,
    step=0.5,
    help="파라과이 강 수위"
)

st.sidebar.divider()
st.sidebar.markdown("### 🎮 Vista 3D")
pitch = st.sidebar.slider("Ángulo de cámara (카메라 각도)", 0, 70, 50)
bearing = st.sidebar.slider("Rotación (회전)", -180, 180, -20)
zoom_level = st.sidebar.slider("Zoom", 9, 14, 11)


# 위험도 계산 함수
def calcular_riesgo(vulnerabilidad, precipitacion, duracion, elevacion, nivel_rio):
    """구역 취약도 + 강우량 + 지속시간 + 고도 + 강 수위로 위험도 계산"""
    intensidad = precipitacion / duracion
    
    # 고도가 낮을수록 위험 증가
    factor_elevacion = max(0, (80 - elevacion) / 40)
    
    # 강 수위가 높을수록 저지대 위험 증가
    factor_rio = (nivel_rio / 5) if elevacion < 60 else 0
    
    score = vulnerabilidad * (precipitacion / 30) * (intensidad / 20) + factor_elevacion + factor_rio
    
    if score < 1.5:
        return "safe", "🟢 Seguro", [34, 197, 94, 200], 0
    elif score < 3:
        return "caution", "🟡 Precaución", [251, 191, 36, 200], 1
    else:
        return "danger", "🔴 Peligro", [239, 68, 68, 200], 2


# 데이터 처리
zona_data = []
alertas = []
zonas_peligro = 0
zonas_precaucion = 0

for zona in zonas:
    nivel, texto, color, risk_level = calcular_riesgo(
        zona["vulnerabilidad"],
        precipitacion,
        duracion,
        zona["elevacion"],
        nivel_rio
    )
    
    if nivel == "danger":
        zonas_peligro += 1
        alertas.append(zona["nombre"])
    elif nivel == "caution":
        zonas_precaucion += 1
    
    zona_data.append({
        "nombre": zona["nombre"],
        "lat": zona["lat"],
        "lon": zona["lon"],
        "elevacion": zona["elevacion"],
        "altura_display": zona["elevacion"] * 20,
        "color": color,
        "risk_level": risk_level,
        "texto": texto
    })

df = pd.DataFrame(zona_data)

# 탭 구성
tab1, tab2, tab3 = st.tabs(["🏔️ Vista 3D Terreno", "🗺️ Mapa 2D", "📊 Análisis"])

# ===== TAB 1: 3D 지형 (메인) =====
with tab1:
    st.subheader("🏔️ Vista 3D del Terreno con Mapbox")
    st.caption("실제 위성 지형 위에 침수 위험도 표시 - 마우스로 드래그하여 회전 가능")
    
    # 지형 고도 컬럼 레이어
    terrain_layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position=["lon", "lat"],
        get_elevation="altura_display",
        elevation_scale=50,
        radius=600,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
        extruded=True,
    )
    
    # 위험 구역 펄스 효과 (ScatterplotLayer)
    danger_zones = df[df["risk_level"] == 2].copy()
    if not danger_zones.empty:
        danger_pulse = pdk.Layer(
            "ScatterplotLayer",
            data=danger_zones,
            get_position=["lon", "lat"],
            get_radius=1200,
            get_fill_color=[239, 68, 68, 80],
            pickable=False,
        )
    else:
        danger_pulse = None
    
    # 침수 영역 시뮬레이션 (저지대)
    low_areas = df[df["elevacion"] < 55].copy()
    water_height = nivel_rio * 100 + precipitacion * 2
    low_areas["water_h"] = water_height
    
    water_layer = pdk.Layer(
        "ColumnLayer",
        data=low_areas,
        get_position=["lon", "lat"],
        get_elevation="water_h",
        elevation_scale=10,
        radius=700,
        get_fill_color=[65, 145, 255, 140],
        pickable=False,
        extruded=True,
    )
    
    # 텍스트 레이블 레이어
    text_layer = pdk.Layer(
        "TextLayer",
        data=df,
        get_position=["lon", "lat"],
        get_text="nombre",
        get_size=14,
        get_color=[255, 255, 255, 255],
        get_angle=0,
        get_text_anchor="'middle'",
        get_alignment_baseline="'bottom'",
        billboard=True,
    )
    
    # 뷰 설정
    view_state = pdk.ViewState(
        latitude=-25.2900,
        longitude=-57.5700,
        zoom=zoom_level,
        pitch=pitch,
        bearing=bearing,
    )
    
    # 툴팁
    tooltip = {
        "html": """
        <div style="padding: 10px;">
            <b style="font-size: 16px;">{nombre}</b><br/>
            <hr style="margin: 5px 0;"/>
            📍 Elevación: <b>{elevacion}m</b><br/>
            {texto}
        </div>
        """,
        "style": {
            "backgroundColor": "rgba(25, 25, 40, 0.9)",
            "color": "white",
            "fontSize": "13px",
            "borderRadius": "8px",
        }
    }
    
    # 레이어 구성
    layers = [water_layer, terrain_layer, text_layer]
    if danger_pulse is not None:
        layers.insert(1, danger_pulse)
    
    # Mapbox 위성+지형 스타일
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip=tooltip,
        map_provider="mapbox",
        map_style="mapbox://styles/mapbox/satellite-streets-v12",
        api_keys={"mapbox": MAPBOX_API_KEY},
    )
    
    st.pydeck_chart(deck)
    
    # 범례
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🟢 **Seguro** - 고지대")
    with col2:
        st.markdown("🟡 **Precaución** - 주의")
    with col3:
        st.markdown("🔴 **Peligro** - 침수 위험")
    with col4:
        st.markdown("🔵 **Agua** - 예상 침수")
    
    # 현재 상태 요약
    st.markdown("---")
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    mcol1.metric("🌧️ 강우량", f"{precipitacion} mm")
    mcol2.metric("⏱️ 지속시간", f"{duracion} h")
    mcol3.metric("🌊 강 수위", f"{nivel_rio} m")
    mcol4.metric("⚠️ 위험구역", f"{zonas_peligro} 개")


# ===== TAB 2: 2D 지도 =====
with tab2:
    st.subheader("🗺️ Mapa de Riesgo 2D")
    
    mapa = folium.Map(
        location=[-25.2867, -57.5800], 
        zoom_start=12,
        tiles="CartoDB positron"
    )
    
    for _, row in df.iterrows():
        color_hex = f'#{row["color"][0]:02x}{row["color"][1]:02x}{row["color"][2]:02x}'
        
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=20,
            popup=f"<b>{row['nombre']}</b><br/>{row['texto']}<br/>Elevación: {row['elevacion']}m",
            color=color_hex,
            fill=True,
            fill_color=color_hex,
            fill_opacity=0.7
        ).add_to(mapa)
        
        folium.Marker(
            location=[row["lat"], row["lon"]],
            icon=folium.DivIcon(
                html=f'<div style="font-size:11px; font-weight:bold; color:#333; background:rgba(255,255,255,0.7); padding:2px 5px; border-radius:3px;">{row["nombre"]}</div>'
            )
        ).add_to(mapa)
    
    st_folium(mapa, width=900, height=500)


# ===== TAB 3: 분석 =====
with tab3:
    st.subheader("📊 Análisis de Riesgo por Zona")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏔️ Perfil de Elevación")
        
        df_sorted = df.sort_values("elevacion", ascending=True)
        chart_data = df_sorted.set_index("nombre")["elevacion"]
        st.bar_chart(chart_data, color="#4A90D9", horizontal=True)
        
        st.caption("⬆️ 높을수록 안전 | ⬇️ 낮을수록 침수 위험")
    
    with col2:
        st.markdown("### ⚠️ Estado de Alertas")
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("🔴 Peligro", f"{zonas_peligro}")
        col_b.metric("🟡 Precaución", f"{zonas_precaucion}")
        col_c.metric("🟢 Seguro", f"{len(zonas) - zonas_peligro - zonas_precaucion}")
        
        if alertas:
            st.error(f"**⚠️ 위험 구역:** {', '.join(alertas)}")
        else:
            st.success("✅ 모든 구역 안전")
    
    st.divider()
    
    st.markdown("### 📋 Datos Detallados")
    
    display_df = df[["nombre", "elevacion", "texto", "risk_level"]].copy()
    display_df.columns = ["구역 (Zona)", "고도 (m)", "상태", "위험도"]
    display_df = display_df.sort_values("위험도", ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)


# ===== 하단 권장 조치 =====
st.divider()
st.subheader("📱 Recomendaciones del Sistema AI")

if zonas_peligro > 0:
    st.error(f"""
    ### 🚨 ALERTA ROJA - 적색 경보
    
    **위험 구역 ({zonas_peligro}개):** {', '.join(alertas)}
    
    | Acción | 조치 사항 |
    |--------|----------|
    | 🚫 Evitar | 빨간 구역 접근 금지 |
    | 🚗 Ruta alternativa | Villa Morra, Recoleta 경유 |
    | 📱 Emergencia | 긴급 알림 활성화 |
    | 🏠 Evacuación | Bañado 지역 대피 준비 |
    """)
elif zonas_precaucion > 0:
    st.warning(f"""
    ### ⚠️ ALERTA AMARILLA - 황색 경보
    
    - 🌊 Monitoree el nivel del río (강 수위 주시)
    - 🛣️ Prepare rutas alternativas (우회 경로 준비)
    - 📻 Esté atento a actualizaciones (기상 업데이트 확인)
    """)
else:
    st.success("""
    ### ✅ SITUACIÓN NORMAL - 정상
    
    - ☀️ No se esperan inundaciones (침수 예상 없음)
    - 🚗 Tráfico normal en todas las zonas (전 구역 교통 정상)
    """)

# 푸터
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    🇰🇷🇵🇾 <b>Cooperación Corea-Paraguay en Smart City</b><br/>
    Prototipo para el Concurso de Video de Ingeniería Global<br/>
    <small>AI-Powered Flood Prediction System v1.0</small>
</div>
""", unsafe_allow_html=True)