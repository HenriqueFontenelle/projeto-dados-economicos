# test_simple.py
import streamlit as st

st.set_page_config(page_title="Teste", layout="wide")

# Sidebar básica
st.sidebar.title("🧪 Teste Sidebar")
st.sidebar.write("Se você vê isso, a sidebar funciona!")

# Conteúdo principal
st.title("🧪 Teste Principal")
st.write("Se você vê isso, o conteúdo principal funciona!")

# Teste de estado
if 'counter' not in st.session_state:
    st.session_state.counter = 0

if st.sidebar.button("Clique aqui"):
    st.session_state.counter += 1

st.sidebar.write(f"Contador: {st.session_state.counter}")
st.write("Se tudo funcionar, você deve ver a sidebar à esquerda!")