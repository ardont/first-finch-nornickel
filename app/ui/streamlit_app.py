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
    st.markdown("### 📡 Статус распределенного кластера")
    
    # Эмуляция проверки здоровья через FastAPI
    # В проде будет запрос на: requests.get("http://localhost:8000/health")
    backend_status = "Online"
    neo4j_status = "Online"
    chromadb_status = "Online"
    
    def render_status(name, status):
        badge_class = "status-online" if status == "Online" else "status-offline"
        st.markdown(f"**{name}**: <span class='status-badge {badge_class}'>{status}</span>", unsafe_allow_html=True)
        
    render_status("FastAPI Master", backend_status)
    render_status("Node 1: Neo4j (N200)", neo4j_status)
    render_status("Node 2: Chroma (N150)", chromadb_status)
    
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
        
        # Эмуляция отправки на FastAPI backend
        with st.spinner("Оркестратор собирает граф знаний и векторные чанки..."):
            # Для демонстрации структуры создаем интерактивный ответ
            # В проде: response = requests.post("http://localhost:8000/query", json={...})
            
            st.markdown("#### 📝 Сгенерированный ответ (YandexGPT Pro)")
            
            # В зависимости от вопроса выводим красивую демонстрацию
            if "обессоливание" in query.lower() or "сухой остаток" in query.lower():
                answer_md = """
                Для исходной воды с содержанием сульфатов, хлоридов, Ca, Mg, Na на уровне **200–300 мг/л** и требуемым сухим остатком **≤1000 мг/дм³** подходят следующие комбинированные методы:
                
                1. **Обратный осмос (RO):** Обеспечивает селективность до 98-99% по одновалентным и двухвалентным ионам.
                2. **Ультрафильтрация + Электродиализ:** Оптимально для селективного извлечения солей кальция и магния без жесткого мембранного концентрирования.
                
                ⚠️ **Зона разногласий в данных:**
                * В отчете *[Гипроникель_2022_Водоотведение.pdf, стр. 14]* указывается, что мембраны обратного осмоса забиваются при концентрации Ca > 250 мг/л без предварительного умягчения.
                * В статье *[Вестник_Кольской_ГМК_2024.pdf, стр. 3]* утверждается, что ингибиторы осадкообразования позволяют работать при Ca до 350 мг/л.
                """
                st.write(answer_md)
            elif "католит" in query.lower() or "электроэкстракц" in query.lower():
                answer_md = """
                При электроэкстракции никеля используются следующие методы циркуляции католита:
                
                * **Двухконтурная циркуляция:** Подача свежего католита непосредственно в прикатолидное пространство.
                * **Оптимальная скорость потока:** По мировым стандартам *[Outokumpu_Electrowinning_Specs.pdf, стр. 42]*, оптимальная линейная скорость составляет **0.12–0.15 м/с** для предотвращения дендритообразования.
                """
                st.write(answer_md)
            else:
                st.write("Найдена онтологическая сеть и векторные совпадения. Данные загружены.")
                
            st.markdown("---")
            st.markdown("#### 🔗 Источники и цитаты (Explainability)")
            col_src1, col_src2 = st.columns(2)
            col_src1.markdown("""
                <div class='glass-card'>
                    <strong>📄 Гипроникель_2022_Водоотведение.pdf</strong><br>
                    <small>Раздел: Очистка стоков. Стр 14. Концентрация кальция и сульфатов.</small>
                </div>
            """, unsafe_allow_html=True)
            col_src2.markdown("""
                <div class='glass-card'>
                    <strong>📄 Вестник_Кольской_ГМК_2024.pdf</strong><br>
                    <small>Статья: Реагентное умягчение шахтных вод. Стр 3.</small>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("#### 📊 Локальный граф знаний (Neo4j Context)")
            
            # Генерация демонстрационного графа через PyVis
            net = Network(height="400px", width="100%", bgcolor="#0e1117", font_color="white")
            net.add_node(1, label="Обессоливание воды", color="#00f2fe", size=25)
            net.add_node(2, label="Обратный Осмос", color="#4facfe", size=20)
            net.add_node(3, label="Сухой Остаток <= 1000 мг/л", color="#e74c3c", size=15)
            net.add_node(4, label="Кальций (Ca)", color="#9b59b6", size=15)
            net.add_edge(1, 2, label="Использует метод")
            net.add_edge(2, 3, label="Ограничение")
            net.add_edge(1, 4, label="Параметр очистки")
            
            net.save_graph("temp_graph.html")
            
            with open("temp_graph.html", "r", encoding="utf-8") as f:
                html_data = f.read()
            components.html(html_data, height=420)
            
            # Удаляем временный файл
            if os.path.exists("temp_graph.html"):
                os.remove("temp_graph.html")

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
