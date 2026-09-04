import streamlit as st

# Minimal translation helper. Use English keys; returns Hindi when selected.
_TRANSLATIONS = {
    "Hindi": {
        "Grow money over time": "समय के साथ पैसा बढ़ाना",
        "Understand risk": "जोखिम समझें",
        "Compare investments": "निवेशों की तुलना करें",
        "Starting amount ($)": "शुरुआती राशि ($)",
        "Monthly contribution ($)": "मासिक योगदान ($)",
        "Time horizon (years)": "समय सीमा (साल)",
        "Run Experiment": "प्रयोग चलाएँ",
        "Run Backtest": "बैकटेस्ट चलाएं",
        "Try QuantLit Demo": "QuantLit डेमो आज़माएं",
        "Simulation assumptions": "सिमुलेशन मान्यताएँ",
    }
}

# Add Spanish translations and a few additional English→Hindi keys used in UI
_TRANSLATIONS["Spanish"] = {
    "Grow money over time": "Hacer crecer el dinero con el tiempo",
    "Understand risk": "Entender el riesgo",
    "Compare investments": "Comparar inversiones",
    "Starting amount ($)": "Monto inicial ($)",
    "Monthly contribution ($)": "Contribución mensual ($)",
    "Time horizon (years)": "Horizonte de tiempo (años)",
    "Run Experiment": "Ejecutar experimento",
    "Run Backtest": "Ejecutar backtest",
    "Try QuantLit Demo": "Probar demo de QuantLit",
    "Simulation assumptions": "Suposiciones de simulación",
    "My Experiments (history & compare)": "Mis experimentos (historial y comparar)",
    "What did I learn": "¿Qué aprendí?",
}

_TRANSLATIONS["Hindi"].update({
    "My Experiments (history & compare)": "मेरे प्रयोग (ऐतिहासिक & तुलना)",
    "What did I learn": "मैंने क्या सीखा",
})


def t(key: str) -> str:
    lang = st.session_state.get("language", "English")
    if lang in _TRANSLATIONS and key in _TRANSLATIONS[lang]:
        return _TRANSLATIONS[lang][key]
    return key
