import streamlit as st
import requests
import json
import os
from pyvis.network import Network
import streamlit.components.v1 as components

# Настройка страницы
st.set_page_config(
    page_title="Научный клубок — GraphRAG Норникель",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Применение премиум стилей CSS (Curated Dark Mode, Outfit Font, Glassmorphism)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@300;400&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Градиентный фон заголовка */
    .hero-title {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .hero-subtitle {
        color: #8892b0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Карточки с эффектом стеклянного размытия */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        border-color: rgba(0, 242, 254, 0.4);
        box-shadow: 0 8px 30px rgba(0, 242, 254, 0.05);
    }
    
    /* Индикаторы статусов */
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-right: 8px;
    }
    .status-online {
        background-color: rgba(46, 204, 113, 0.15);
        color: #2ecc71;
        border: 1px solid rgba(46, 204, 113, 0.3);
    }
    .status-offline {
        background-color: rgba(231, 76, 60, 0.15);
        color: #e74c3c;
        border: 1px solid rgba(231, 76, 60, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# Инициализация состояния
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Боковая панель управления (Фильтры и статус нод)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/ec/Nornickel_logo.svg", width=180)
    st.markdown("### 🎛️ Фильтры и Управление")
    
    role = st.selectbox("🔑 Ролевой доступ (ИБ):", ["Исследователь (Все данные)", "Партнер (Публичные данные)"], index=0)
    geography = st.selectbox("🌍 Географический срез:", ["Все регионы", "Только РФ", "Зарубежные практики"], index=0)
    year_from = st.slider("📅 Год публикаций с:", min_value=2015, max_value=2026, value=2021)
    
    st.markdown("---")
    st.subheader("⚙️ Настройки сети Tailscale")
    default_api = os.getenv("BACKEND_API_URL", "http://100.71.14.9:8000")
    backend_url = st.text_input("URL бэкенда (FastAPI):", value=default_api)
    
    st.markdown("### 📡 Статус распределенного кластера")
    
    # Запрос реального статуса здоровья нод через FastAPI
    backend_status = "Offline"
    neo4j_status = "Offline"
    chromadb_status = "Offline"
    
    try:
        res = requests.get(f"{backend_url}/health", timeout=2)
        if res.status_code == 200:
            health_data = res.json()
            backend_status = "Online" if health_data.get("status") == "healthy" or health_data.get("status") == "degraded" else "Offline"
            neo4j_status = "Online" if "error" not in health_data.get("neo4j", "") else "Offline"
            chromadb_status = "Online" if "error" not in health_data.get("chromadb", "") else "Offline"
    except Exception:
        pass
    
    def render_status(name, status):
        badge_class = "status-online" if status == "Online" else "status-offline"
        st.markdown(f"**{name}**: <span class='status-badge {badge_class}'>{status}</span>", unsafe_allow_html=True)
        
    render_status("FastAPI Master", backend_status)
    render_status("Node 1: Neo4j (N200)", neo4j_status)
    render_status("Node 2: Chroma (N150)", chromadb_status)
    
    # Кнопка ручной проверки
    if st.button("📡 Проверить пинг до бэкенда"):
        st.rerun()
        
    st.markdown("---")
    st.markdown("💡 *Кластер объединен Mesh-сетью Tailscale с шифрованием трафика.*")

# Главный экран
st.markdown("<h1 class='hero-title'>Научный клубок</h1>", unsafe_allow_html=True)
st.markdown("<p class='hero-subtitle'>Распределенная система GraphRAG онтологий и семантического поиска R&D Норникеля</p>", unsafe_allow_html=True)

# Создание вкладок для различных режимов
tabs = st.tabs(["🔍 Интеллектуальный поиск", "📊 Анализ белых пятен (Gap Analysis)", "🎓 Радар Экспертов"])

with tabs[0]:
    st.markdown("### 💬 Запрос к базе знаний R&D")
    
    # 4 эталонных вопроса в качестве подсказок
    st.markdown("**Часто задаваемые вопросы (Бенчмарки):**")
    cols = st.columns(4)
    benchmarks = [
        "Обессоливание воды с солями 200-300 мг/л и сухим остатком <=1000 мг/дм3",
        "Циркуляция католита при электроэкстракции никеля и оптимальная скорость",
        "Распределение Au, Ag и МПГ между штейном и шлаком с 2021 года",
        "Закачка шахтных вод в глубокие горизонты РФ vs Мировая практика и ТЭП"
    ]
    
    query = st.chat_input("Введите ваш научно-технический вопрос...")
    
    # Клик по бенчмаркам
    for i, q_text in enumerate(benchmarks):
        if cols[i].button(q_text[:40] + "...", key=f"btn_{i}", help=q_text):
            query = q_text
            
    if query:
        st.chat_message("user").write(query)
        
        # Подготовка фильтров для отправки на FastAPI backend
        payload = {
            "query": query,
            "geography": "all" if geography == "Все регионы" else ("RU" if geography == "Только РФ" else "GLOBAL"),
            "year_from": year_from,
            "role": "researcher" if "Исследователь" in role else "partner"
        }
        
        with st.spinner("Оркестратор собирает граф знаний и векторные чанки по сети Tailscale..."):
            try:
                response = requests.post(f"{backend_url}/query", json=payload, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    
                    st.markdown("#### 📝 Сгенерированный ответ (YandexGPT Pro)")
                    st.write(result["answer"])
                    
                    st.markdown("---")
                    st.markdown("#### 🔗 Источники и цитаты (Explainability)")
                    
                    sources = result.get("sources", [])
                    if sources:
                        # Рендерим карточки источников
                        cols_src = st.columns(min(len(sources), 3))
                        for idx, src in enumerate(sources[:3]):
                            col_idx = idx % 3
                            src_meta = src.get("metadata", {})
                            cols_src[col_idx].markdown(f"""
                                <div class='glass-card'>
                                    <strong>📄 {src_meta.get('source', 'Неизвестный файл')}</strong><br>
                                    <small>Год: {src_meta.get('year', 'Не указан')}, Регион: {src_meta.get('geography', 'Все')}</small><br>
                                    <p style="font-size:0.85rem; color:#8892b0; margin-top:8px;">"{src.get('text', '')[:140]}..."</p>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("Векторные источники не найдены в коллекции ChromaDB.")
                    
                    st.markdown("---")
                    st.markdown("#### 📊 Локальный граф знаний (Neo4j Subgraph)")
                    
                    subgraph = result.get("subgraph", [])
                    if subgraph:
                        # Цветовая гамма для разных типов сущностей
                        color_map = {
                            "Experiment": "#00f2fe",
                            "Material": "#2ecc71",
                            "Condition": "#f1c40f",
                            "Property": "#e74c3c",
                            "Expert": "#e67e22",
                            "Equipment": "#9b59b6",
                            "Publication": "#34495e",
                            "Facility": "#1abc9c",
                            "Parameter": "#f1c40f"
                        }
                        
                        net = Network(height="450px", width="100%", bgcolor="#0e1117", font_color="white")
                        
                        nodes_added = set()
                        for edge in subgraph:
                            src_name = edge["source"]
                            src_type = edge["source_type"]
                            tgt_name = edge["target"]
                            tgt_type = edge["target_type"]
                            rel = edge["relationship"]
                            
                            # Добавляем исходный узел
                            if src_name not in nodes_added:
                                color = color_map.get(src_type, "#bdc3c7")
                                net.add_node(src_name, label=src_name, color=color, size=20, title=f"Тип: {src_type}")
                                nodes_added.add(src_name)
                                
                            # Добавляем целевой узел
                            if tgt_name not in nodes_added:
                                color = color_map.get(tgt_type, "#bdc3c7")
                                net.add_node(tgt_name, label=tgt_name, color=color, size=20, title=f"Тип: {tgt_type}")
                                nodes_added.add(tgt_name)
                                
                            # Добавляем ребро
                            net.add_edge(src_name, tgt_name, label=rel)
                            
                        # Сохраняем и рендерим граф
                        graph_html_path = "temp_query_graph.html"
                        net.save_graph(graph_html_path)
                        
                        with open(graph_html_path, "r", encoding="utf-8") as f:
                            html_data = f.read()
                        components.html(html_data, height=470)
                        
                        # Удаляем временный файл
                        if os.path.exists(graph_html_path):
                            os.remove(graph_html_path)
                    else:
                        st.info("Релевантные связи в графе знаний Neo4j не обнаружены.")
                else:
                    st.error(f"Ошибка бэкенда FastAPI: {response.text}")
            except Exception as e:
                st.error(f"Не удалось отправить запрос к бэкенду по Tailscale: {e}")

with tabs[1]:
    st.markdown("### 📊 Радар Белых Пятен (Gap Analysis)")
    st.markdown("Анализ пробелов в исследованиях сплавов, металлов и технологических режимов.")
    
    # Таблица "белых пятен"
    data = {
        "Технология очистки / сплав": ["Обратный осмос", "Электродиализ", "Ультрафильтрация", "Ионный обмен"],
        "Сульфаты (>300 мг/л)": ["Исследовано ✅", "Исследовано ✅", "Пробел в данных ⚠️", "Исследовано ✅"],
        "Хлориды (>500 мг/л)": ["Пробел в данных ⚠️", "Исследовано ✅", "Пробел в данных ⚠️", "Пробел в данных ⚠️"],
        "Кальций (>300 мг/л)": ["Исследовано ✅", "Пробел в данных ⚠️", "Исследовано ✅", "Исследовано ✅"]
    }
    st.table(data)
    st.markdown("⚠️ *Исследования по ультрафильтрации хлоридов высокой концентрации отсутствуют в архивах Гипроникеля с 2021 года. Рекомендуется планирование опытно-промышленных испытаний (ОПИ).*")

with tabs[2]:
    st.markdown("### 🎓 Профильный Радар Экспертов")
    st.markdown("Автоматический подбор профильных специалистов по теме поискового запроса на основе публикаций и отчетов:")
    
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        st.markdown("""
            <div class='glass-card'>
                <h4>👴 Цымбулов Леонид Борисович</h4>
                <p><strong>Специализация:</strong> Пирометаллургия, плавка штейнов, распределение благородных металлов.</p>
                <p>📧 l.tsymbulov@nornik.ru | 📞 Вн. тел: 54-12</p>
                <small>Найдено совпадений в отчетах: 14</small>
            </div>
        """, unsafe_allow_html=True)
    with col_exp2:
        st.markdown("""
            <div class='glass-card'>
                <h4>👨 Румянцев Александр Евгеньевич</h4>
                <p><strong>Специализация:</strong> Водоподготовка, очистка шахтных вод обогатительных фабрик.</p>
                <p>📧 a.rumyantsev@nornik.ru | 📞 Вн. тел: 32-09</p>
                <small>Найдено совпадений в отчетах: 8</small>
            </div>
        """, unsafe_allow_html=True)
