import streamlit as st

st.set_page_config(page_title="论文工具集", layout="wide")
st.title("📚 论文数据处理工具集")

st.markdown("""
欢迎使用本工具集，包含两个子功能（请通过左侧侧边栏选择页面）：

1. **🌐 DBLP 抓取器**：从 DBLP 抓取多会议论文，并按关键词过滤。
2. **📊 可视化分析**：对分主题的论文信息进行按主题可视化。（当前数据更新至5月4日，不包含PPoPP会议）
""")
