import streamlit as st
import pandas as pd
import re
from pathlib import Path
import altair as alt

# --- 配置 ---
PAPERS_DIR = Path("papers")  # 存放 .md 文件的目录

# --- 解析函数 ---
def parse_markdown(file_path):
    """
    解析单个 Markdown 文件，提取主题、标题、年份、会议名称、会议年份和链接
    返回列表 of dict
    """
    records = []
    text = file_path.read_text(encoding='utf-8')
    entries = re.split(r"^##+", text, flags=re.MULTILINE)
    theme = file_path.stem
    for entry in entries:
        title_match = re.match(r"\s*\d+\.\s*(.*)", entry)
        if not title_match:
            continue
        title = title_match.group(1).strip()
        # 提取完整 Conference 字段
        conf_line = re.search(r"Conference:\s*([^\n]+)", entry)
        conference_name = None
        conference_year = None
        if conf_line:
            # 例如 'ATC 2023' 或 'EuroSys 2025'
            parts = conf_line.group(1).strip().rsplit(' ', 1)
            if len(parts) == 2 and parts[1].isdigit():
                conference_name, year_str = parts
                conference_year = int(year_str)
            else:
                conference_name = conf_line.group(1).strip()
        url_match = re.search(r"- URL:\s*\[.*?\]\((.*?)\)", entry)
        url = url_match.group(1).strip() if url_match else None
        # 冗余年份，以会议字段为准
        if conference_year:
            records.append({
                'theme': theme,
                'title': title,
                'year': conference_year,
                'conference': conference_name,
                'url': url
            })
    return records

@st.cache_data
def load_data():
    all_records = []
    if not PAPERS_DIR.exists():
        return pd.DataFrame(columns=['theme','title','year','conference','url'])
    for md_file in PAPERS_DIR.glob("*.md"):
        all_records.extend(parse_markdown(md_file))
    return pd.DataFrame(all_records)

# --- 主程序 ---
def main():
    # st.title("按主题分布的论文可视化")
    df = load_data()
    if df.empty:
        st.warning(f"未在 {PAPERS_DIR}/ 目录下找到有效的 .md 文件。")
        return

    # 侧边栏：主题选择
    st.sidebar.header("选择主题")
    themes = sorted(df['theme'].unique().tolist())
    selected = st.sidebar.multiselect("主题", themes, default=[])
    if not selected:
        st.info("请选择至少一个主题进行展示。")
        return

    for theme in selected:
        st.header(f"主题：{theme}")
        sub_df = df[df['theme'] == theme]

        # 主要会议年度分布（堆叠柱状图）
        st.subheader("主要会议年度分布（堆叠柱状图）")
        conf_df = sub_df.groupby(['year','conference']).size().reset_index(name='count')
        chart_conf = alt.Chart(conf_df).mark_bar().encode(
            x=alt.X('year:O', title='Year'),
            y=alt.Y('count:Q', title='Count'),
            color=alt.Color('conference:N', title='Conference', legend=alt.Legend(orient='right')),
            tooltip=['conference','year','count']
        ).properties(width=650)
        st.altair_chart(chart_conf, use_container_width=True)

        # 论文列表
        st.subheader("论文列表")
        for year in sorted(sub_df['year'].unique()):
            yearly = sub_df[sub_df['year'] == year]
            with st.expander(f"{year} 年 ({len(yearly)} 篇)"):
                for _, row in yearly.iterrows():
                    if row['url']:
                        st.markdown(f"- [{row['title']}]({row['url']}) ({row['conference']} {row['year']})")
                    else:
                        st.markdown(f"- **{row['title']}** ({row['conference']} {row['year']})")

if __name__ == '__main__':
    main()
