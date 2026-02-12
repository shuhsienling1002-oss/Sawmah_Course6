import streamlit as st
import streamlit.components.v1 as components
import random
import re
import time
from gtts import gTTS
from io import BytesIO

# --- 0. 系統配置 (System Configuration) ---
st.set_page_config(
    page_title="I lalan - 街頭對話", 
    page_icon="🚦", 
    layout="centered"
)

# --- 1. 資料庫 (第 6 課：I lalan) ---
VOCAB_MAP = {
    "talacowa": "去哪裡", "kiso": "你", "talapaisingan": "去醫院", 
    "kako": "我", "mamaan": "怎麼了", "adada": "痛/病", 
    "ko": "主格標記", "tiyad": "肚子", "ako": "我的", 
    "kalamkamen": "趕快", "a": "連接詞", "tayra": "去那裡",
    "icowa": "哪裡", "ising": "醫生", "paisingan": "醫院",
    "fongoh": "頭", "wa'ay": "腳", "tayni": "來這裡"
}

VOCABULARY = [
    {"amis": "talacowa", "zh": "去哪裡", "emoji": "❓", "root": "icowa", "root_zh": "哪裡"},
    {"amis": "talapaisingan", "zh": "去醫院", "emoji": "🏥", "root": "ising", "root_zh": "醫生"},
    {"amis": "mamaan", "zh": "怎麼了", "emoji": "😧", "root": "maan", "root_zh": "什麼"},
    {"amis": "adada", "zh": "痛/病", "emoji": "💥", "root": "adada", "root_zh": "痛"},
    {"amis": "tiyad", "zh": "肚子", "emoji": "🤢", "root": "tiyad", "root_zh": "肚子"},
    {"amis": "kalamkamen", "zh": "趕快", "emoji": "🏃", "root": "kalamkam", "root_zh": "快"},
    {"amis": "tayra", "zh": "去那裡", "emoji": "👉", "root": "ra", "root_zh": "那裡"},
    {"amis": "tala-", "zh": "前往(前綴)", "emoji": "🚶", "root": "tala", "root_zh": "去"},
    {"amis": "paisingan", "zh": "醫院", "emoji": "🚑", "root": "ising", "root_zh": "醫生"},
    {"amis": "fongoh", "zh": "頭", "emoji": "🤕", "root": "fongoh", "root_zh": "頭"},
]

SENTENCES = [
    {
        "amis": "Talacowa kiso?", 
        "zh": "你要去哪裡？", 
        "note": """
        <br><b>Talacowa</b>：去哪裡 (<i>tala-</i> 去 + <i>icowa</i> 哪裡)。
        <br><b>kiso</b>：你。
        <br><b>用途</b>：最常見的見面問候語。"""
    },
    {
        "amis": "Talapaisingan kako.", 
        "zh": "我要去醫院。", 
        "note": """
        <br><b>Talapaisingan</b>：去醫院。
        <br><b>結構</b>：<i>tala-</i> (去) + <i>pa-ising-an</i> (醫院/看病處)。
        <br><b>ising</b>：醫生/藥。"""
    },
    {
        "amis": "Mamaan kiso?", 
        "zh": "你怎麼了？", 
        "note": """
        <br><b>Mamaan</b>：發生什麼事/怎麼了。
        <br><b>maan</b>：什麼。
        <br><b>語境</b>：看到對方臉色不好或受傷時的關心用語。"""
    },
    {
        "amis": "Adada ko tiyad ako.", 
        "zh": "我的肚子痛。", 
        "note": """
        <br><b>Adada</b>：痛 (狀態動詞)。
        <br><b>tiyad</b>：肚子。
        <br><b>句型</b>：Adada ko [身體部位] [屬格]。"""
    },
    {
        "amis": "Kalamkamen a tayra.", 
        "zh": "趕快去那裡吧。", 
        "note": """
        <br><b>Kalamkamen</b>：趕快 (命令/建議)。
        <br><b>tayra</b>：去那裡 (遠離說話者)。
        <br><b>對比</b>：<i>Tayni</i> (來這裡)。"""
    }
]

STORY_DATA = [
    {"amis": "Talacowa kiso?", "zh": "你要去哪裡？"},
    {"amis": "Talapaisingan kako.", "zh": "我要去醫院。"},
    {"amis": "Mamaan kiso?", "zh": "你怎麼了？"},
    {"amis": "Adada ko tiyad ako.", "zh": "我的肚子痛。"},
    {"amis": "Kalamkamen a tayra.", "zh": "趕快去那裡吧。"}
]

# --- 2. 視覺系統 (CSS 注入 - Urban Transit Theme) ---
st.markdown("""
    <style>
    /* 引入 Barlow (交通導視風) 和 Noto Sans TC */
    @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;800&family=Noto+Sans+TC:wght@300;500;700&display=swap');
    
    /* 背景：明亮街道灰 */
    .stApp { background-color: #F5F5F5; color: #212121; font-family: 'Noto Sans TC', sans-serif; }
    
    /* 頭部：路標風格 */
    .header-container { 
        background: #2962FF; 
        border-radius: 8px; 
        padding: 25px; 
        text-align: left; 
        margin-bottom: 30px; 
        box-shadow: 0 4px 15px rgba(41, 98, 255, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    /* 裝飾性箭頭 */
    .header-container::before {
        content: '➔';
        position: absolute;
        right: 20px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 80px;
        color: rgba(255, 255, 255, 0.2);
        font-weight: bold;
    }
    
    .main-title { 
        font-family: 'Barlow', sans-serif; 
        color: #FFFFFF; 
        font-size: 48px; 
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 5px; 
        letter-spacing: 2px;
    }
    
    .sub-title { 
        color: #E3F2FD; 
        font-size: 18px; 
        font-family: 'Barlow', sans-serif;
        font-weight: 600;
        letter-spacing: 1px;
    }
    
    /* Tab 樣式：簡潔線條 */
    .stTabs [data-baseweb="tab"] { 
        color: #757575 !important; 
        font-family: 'Barlow', sans-serif;
        font-size: 18px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] { 
        border-bottom: 4px solid #2962FF !important; 
        color: #2962FF !important; 
    }
    
    /* 按鈕：交通標誌藍 */
    .stButton>button { 
        border: none !important; 
        background: #2962FF !important; 
        color: #FFFFFF !important; 
        font-family: 'Barlow', sans-serif !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        width: 100%; 
        border-radius: 4px; 
        transition: 0.2s; 
        text-transform: uppercase;
    }
    .stButton>button:hover { 
        background: #1565C0 !important; 
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* 測驗卡片：票卡風格 */
    .quiz-card { 
        background: #FFFFFF; 
        border-left: 6px solid #2962FF; 
        padding: 25px; 
        border-radius: 4px; 
        margin-bottom: 20px; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }
    .quiz-tag { 
        background: #212121; 
        color: #FFF; 
        padding: 4px 10px; 
        border-radius: 2px; 
        font-weight: bold; 
        font-size: 12px; 
        margin-right: 10px; 
        font-family: 'Barlow', sans-serif;
        text-transform: uppercase;
    }
    
    /* 翻譯區塊：資訊看板風格 */
    .zh-translation-block {
        background: #E0E0E0;
        border-top: 4px solid #424242;
        padding: 20px;
        margin-top: 0px; 
        color: #424242;
        font-size: 16px;
        line-height: 2.0;
        font-family: 'Noto Sans TC', monospace;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心技術：沙盒渲染引擎 (v9.6 - Transit Edition) ---
def get_html_card(item, type="word"):
    pt = "100px" if type == "full_amis_block" else "80px"
    mt = "-40px" if type == "full_amis_block" else "-30px" 

    style_block = f"""<style>
        @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;800&family=Noto+Sans+TC:wght@300;500;700&display=swap');
        body {{ background-color: transparent; color: #212121; font-family: 'Noto Sans TC', sans-serif; margin: 0; padding: 5px; padding-top: {pt}; overflow-x: hidden; }}
        
        /* 互動單字：交通藍底線 */
        .interactive-word {{ position: relative; display: inline-block; border-bottom: 3px solid #90CAF9; cursor: pointer; margin: 0 3px; color: #212121; transition: 0.3s; font-size: 19px; font-weight: 500; }}
        .interactive-word:hover {{ color: #2962FF; border-bottom-color: #2962FF; }}
        
        .interactive-word .tooltip-text {{ visibility: hidden; min-width: 80px; background-color: #212121; color: #FFF; text-align: center; border-radius: 4px; padding: 6px; position: absolute; z-index: 100; bottom: 145%; left: 50%; transform: translateX(-50%); opacity: 0; transition: opacity 0.3s; font-size: 14px; white-space: nowrap; box-shadow: 0 4px 10px rgba(0,0,0,0.2); font-family: 'Barlow', sans-serif; }}
        .interactive-word:hover .tooltip-text {{ visibility: visible; opacity: 1; }}
        
        .play-btn-inline {{ background: #2962FF; border: none; color: #FFF; border-radius: 50%; width: 28px; height: 28px; cursor: pointer; margin-left: 8px; display: inline-flex; align-items: center; justify-content: center; font-size: 14px; transition: 0.3s; vertical-align: middle; }}
        .play-btn-inline:hover {{ background: #000; transform: scale(1.1); }}
        
        /* 單字卡樣式 - 簡潔卡片 */
        .word-card-static {{ background: #FFFFFF; border: 1px solid #E0E0E0; border-left: 5px solid #2962FF; padding: 15px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; margin-top: {mt}; height: 100px; box-sizing: border-box; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        .wc-root-tag {{ font-size: 12px; background: #E3F2FD; color: #1565C0; padding: 3px 8px; border-radius: 2px; font-weight: bold; margin-right: 5px; font-family: 'Barlow', sans-serif; text-transform: uppercase; }}
        .wc-amis {{ color: #2962FF; font-size: 26px; font-weight: 800; margin: 2px 0; font-family: 'Barlow', sans-serif; letter-spacing: 0.5px; }}
        .wc-zh {{ color: #757575; font-size: 16px; }}
        .play-btn-large {{ background: #FFFFFF; border: 2px solid #2962FF; color: #2962FF; border-radius: 50%; width: 42px; height: 42px; cursor: pointer; font-size: 20px; transition: 0.2s; }}
        .play-btn-large:hover {{ background: #2962FF; color: #FFF; }}
        
        .amis-full-block {{ line-height: 2.2; font-size: 18px; margin-top: {mt}; }}
        .sentence-row {{ margin-bottom: 12px; display: block; }}
    </style>
    <script>
        function speak(text) {{ window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance(); msg.text = text; msg.lang = 'id-ID'; msg.rate = 0.9; window.speechSynthesis.speak(msg); }}
    </script>"""

    header = f"<!DOCTYPE html><html><head>{style_block}</head><body>"
    body = ""
    
    if type == "word":
        v = item
        body = f"""<div class="word-card-static">
            <div>
                <div style="margin-bottom:5px;"><span class="wc-root-tag">ROOT: {v['root']}</span> <span style="font-size:12px; color:#9E9E9E;">({v['root_zh']})</span></div>
                <div class="wc-amis">{v['emoji']} {v['amis']}</div>
                <div class="wc-zh">{v['zh']}</div>
            </div>
            <button class="play-btn-large" onclick="speak('{v['amis'].replace("'", "\\'")}')">🔊</button>
        </div>"""

    elif type == "full_amis_block": 
        all_sentences_html = []
        for sentence_data in item:
            s_amis = sentence_data['amis']
            words = s_amis.split()
            parts = []
            for w in words:
                clean_word = re.sub(r"[^\w']", "", w).lower()
                translation = VOCAB_MAP.get(clean_word, "")
                js_word = clean_word.replace("'", "\\'") 
                
                if translation:
                    chunk = f'<span class="interactive-word" onclick="speak(\'{js_word}\')">{w}<span class="tooltip-text">{translation}</span></span>'
                else:
                    chunk = f'<span class="interactive-word" onclick="speak(\'{js_word}\')">{w}</span>'
                parts.append(chunk)
            
            full_amis_js = s_amis.replace("'", "\\'")
            sentence_html = f"""
            <div class="sentence-row">
                {' '.join(parts)}
                <button class="play-btn-inline" onclick="speak('{full_amis_js}')" title="播放此句">🔊</button>
            </div>
            """
            all_sentences_html.append(sentence_html)
            
        body = f"""<div class="amis-full-block">{''.join(all_sentences_html)}</div>"""
    
    elif type == "sentence": 
        s = item
        words = s['amis'].split()
        parts = []
        for w in words:
            clean_word = re.sub(r"[^\w']", "", w).lower()
            translation = VOCAB_MAP.get(clean_word, "")
            js_word = clean_word.replace("'", "\\'") 
            
            if translation:
                chunk = f'<span class="interactive-word" onclick="speak(\'{js_word}\')">{w}<span class="tooltip-text">{translation}</span></span>'
            else:
                chunk = f'<span class="interactive-word" onclick="speak(\'{js_word}\')">{w}</span>'
            parts.append(chunk)
            
        full_js = s['amis'].replace("'", "\\'")
        body = f'<div style="font-size: 18px; line-height: 1.6; margin-top: {mt};">{" ".join(parts)}</div><button style="margin-top:10px; background:#2962FF; border:none; color:#FFF; padding:6px 15px; border-radius:4px; cursor:pointer; font-family:Barlow; font-weight:600; letter-spacing:1px;" onclick="speak(`{full_js}`)">▶ PLAY AUDIO</button>'

    return header + body + "</body></html>"

# --- 4. 測驗生成引擎 ---
def generate_quiz():
    questions = []
    
    # 1. 聽音辨義
    q1 = random.choice(VOCABULARY)
    q1_opts = [q1['amis']] + [v['amis'] for v in random.sample([x for x in VOCABULARY if x != q1], 2)]
    random.shuffle(q1_opts)
    questions.append({"type": "listen", "tag": "🎧 聽音辨義", "text": "請聽語音，選擇正確的單字", "audio": q1['amis'], "correct": q1['amis'], "options": q1_opts})
    
    # 2. 中翻阿
    q2 = random.choice(VOCABULARY)
    q2_opts = [q2['amis']] + [v['amis'] for v in random.sample([x for x in VOCABULARY if x != q2], 2)]
    random.shuffle(q2_opts)
    questions.append({"type": "trans", "tag": "🧩 中翻阿", "text": f"請選擇「<span style='color:#2962FF'>{q2['zh']}</span>」的阿美語", "correct": q2['amis'], "options": q2_opts})
    
    # 3. 阿翻中
    q3 = random.choice(VOCABULARY)
    q3_opts = [q3['zh']] + [v['zh'] for v in random.sample([x for x in VOCABULARY if x != q3], 2)]
    random.shuffle(q3_opts)
    questions.append({"type": "trans_a2z", "tag": "🔄 阿翻中", "text": f"單字 <span style='color:#2962FF'>{q3['amis']}</span> 的意思是？", "correct": q3['zh'], "options": q3_opts})

    # 4. 詞根偵探
    q4 = random.choice(VOCABULARY)
    other_roots = list(set([v['root'] for v in VOCABULARY if v['root'] != q4['root']]))
    if len(other_roots) < 2: other_roots += ["roma", "lalan", "cidal"]
    q4_opts = [q4['root']] + random.sample(other_roots, 2)
    random.shuffle(q4_opts)
    questions.append({"type": "root", "tag": "🧬 詞根偵探", "text": f"單字 <span style='color:#2962FF'>{q4['amis']}</span> 的詞根是？", "correct": q4['root'], "options": q4_opts, "note": f"詞根意思：{q4['root_zh']}"})
    
    # 5. 語感聽解
    q5 = random.choice(STORY_DATA)
    questions.append({"type": "listen_sent", "tag": "🔊 語感聽解", "text": "請聽句子，選擇正確的中文翻譯", "audio": q5['amis'], "correct": q5['zh'], "options": [q5['zh']] + [s['zh'] for s in random.sample([x for x in STORY_DATA if x != q5], 2)]})

    # 6. 句型翻譯
    q6 = random.choice(STORY_DATA)
    q6_opts = [q6['amis']] + [s['amis'] for s in random.sample([x for x in STORY_DATA if x != q6], 2)]
    random.shuffle(q6_opts)
    questions.append({"type": "sent_trans", "tag": "📝 句型翻譯", "text": f"請選擇中文「<span style='color:#2962FF'>{q6['zh']}</span>」對應的阿美語", "correct": q6['amis'], "options": q6_opts})

    # 7. 克漏字
    q7 = random.choice(STORY_DATA)
    words = q7['amis'].split()
    valid_indices = []
    for i, w in enumerate(words):
        clean_w = re.sub(r"[^\w']", "", w).lower()
        if clean_w in VOCAB_MAP:
            valid_indices.append(i)
    
    if valid_indices:
        target_idx = random.choice(valid_indices)
        target_raw = words[target_idx]
        target_clean = re.sub(r"[^\w']", "", target_raw).lower()
        
        words_display = words[:]
        words_display[target_idx] = "______"
        q_text = " ".join(words_display)
        
        correct_ans = target_clean
        distractors = [k for k in VOCAB_MAP.keys() if k != correct_ans and len(k) > 2]
        if len(distractors) < 2: distractors += ["kako", "ira"]
        opts = [correct_ans] + random.sample(distractors, 2)
        random.shuffle(opts)
        
        questions.append({"type": "cloze", "tag": "🕳️ 文法克漏字", "text": f"請填空：<br><span style='color:#212121; font-size:18px;'>{q_text}</span><br><span style='color:#757575; font-size:14px;'>{q7['zh']}</span>", "correct": correct_ans, "options": opts})
    else:
        questions.append(questions[0]) 

    questions.append(random.choice(questions[:4])) 
    random.shuffle(questions)
    return questions

def play_audio_backend(text):
    try:
        tts = gTTS(text=text, lang='id'); fp = BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3')
    except: pass

# --- 5. UI 呈現層 ---
st.markdown("""
<div class="header-container">
    <h1 class="main-title">I lalan</h1>
    <div class="sub-title">第 6 課：街頭對話</div>
    <div style="font-size: 12px; margin-top:10px; color:#E3F2FD; font-family: 'Barlow', sans-serif;">Code-CRF v6.4 | Theme: Urban Transit</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🚦 互動課文", 
    "🏥 核心單字", 
    "🧬 句型解析", 
    "⚔️ 實戰測驗"
])

with tab1:
    st.markdown("### // 文章閱讀")
    st.caption("👆 點擊單字可聽發音並查看翻譯")
    
    st.markdown("""<div style="background:#FFFFFF; padding:10px; border: 1px solid #E0E0E0; border-left: 5px solid #2962FF; border-radius:4px;">""", unsafe_allow_html=True)
    components.html(get_html_card(STORY_DATA, type="full_amis_block"), height=400, scrolling=True)
    st.markdown("</div>", unsafe_allow_html=True)

    zh_content = "<br>".join([item['zh'] for item in STORY_DATA])
    st.markdown(f"""
    <div class="zh-translation-block">
        {zh_content}
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.markdown("### // 單字與詞根")
    for v in VOCABULARY:
        components.html(get_html_card(v, type="word"), height=150)

with tab3:
    st.markdown("### // 語法結構分析")
    for s in SENTENCES:
        st.markdown("""<div style="background:#FFFFFF; padding:15px; border:1px dashed #BDBDBD; border-radius: 4px; margin-bottom:15px;">""", unsafe_allow_html=True)
        components.html(get_html_card(s, type="sentence"), height=160)
        st.markdown(f"""
        <div style="color:#212121; font-size:16px; margin-bottom:10px; border-top:1px solid #E0E0E0; padding-top:10px;">{s['zh']}</div>
        <div style="color:#757575; font-size:14px; line-height:1.8; border-top:1px dashed #E0E0E0; padding-top:5px;"><span style="color:#2962FF; font-family:Barlow; font-weight:bold;">ANALYSIS:</span> {s.get('note', '')}</div>
        </div>
        """, unsafe_allow_html=True)

with tab4:
    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = generate_quiz()
        st.session_state.quiz_step = 0; st.session_state.quiz_score = 0
    
    if st.session_state.quiz_step < len(st.session_state.quiz_questions):
        q = st.session_state.quiz_questions[st.session_state.quiz_step]
        st.markdown(f"""<div class="quiz-card"><div style="margin-bottom:10px;"><span class="quiz-tag">{q['tag']}</span> <span style="color:#757575;">Q{st.session_state.quiz_step + 1}</span></div><div style="font-size:18px; color:#212121; margin-bottom:10px;">{q['text']}</div></div>""", unsafe_allow_html=True)
        if 'audio' in q: play_audio_backend(q['audio'])
        opts = q['options']; cols = st.columns(min(len(opts), 3))
        for i, opt in enumerate(opts):
            with cols[i % 3]:
                if st.button(opt, key=f"q_{st.session_state.quiz_step}_{i}"):
                    if opt.lower() == q['correct'].lower():
                        st.success("✅ 正確 (Correct)"); st.session_state.quiz_score += 1
                    else:
                        st.error(f"❌ 錯誤 - 正解: {q['correct']}"); 
                        if 'note' in q: st.info(q['note'])
                    time.sleep(1.5); st.session_state.quiz_step += 1; st.rerun()
    else:
        st.markdown(f"""<div style="text-align:center; padding:30px; border:4px solid #2962FF; border-radius:8px; background:#FFFFFF;"><h2 style="color:#2962FF; font-family:Barlow;">MISSION COMPLETE</h2><p style="font-size:20px; color:#212121;">得分: {st.session_state.quiz_score} / {len(st.session_state.quiz_questions)}</p></div>""", unsafe_allow_html=True)
        if st.button("🔄 重新挑戰 (Reboot)"): del st.session_state.quiz_questions; st.rerun()

st.markdown("---")
st.caption("Powered by Code-CRF v6.4 | Architecture: Chief Architect")
