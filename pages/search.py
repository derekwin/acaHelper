import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import concurrent.futures
import io

st.set_page_config(page_title="DBLP 多会议论文筛选器", layout="wide")
st.title("DBLP 论文筛选工具")

# 会议选项
st.markdown("### 选择会议")
conference_options = [
    "OSDI", "ATC", "EuroSys", "ASPLOS", "FAST", "SOSP", "ISCA",
    "SC", "HPCA", "DAC", "MICRO", "SIGCOMM", "MobiCom",
    "INFOCOM", "NSDI", "CoNEXT", "CCS", "S&P", "USENIX Security", "NDSS", "PPoPP"
]

# 全选按钮
if 'select_all_confs' not in st.session_state:
    st.session_state.select_all_confs = False

if st.button("全选会议", key="all_confs_btn"):
    st.session_state.select_all_confs = not st.session_state.select_all_confs

selected_confs = []
cols = st.columns(4)
for idx, conf in enumerate(conference_options):
    with cols[idx % 4]:
        if st.checkbox(conf, key=f"conf_{conf}", value=st.session_state.select_all_confs):
            selected_confs.append(conf)

# 年份选项
st.markdown("### 选择年份")
yearcount = 6
current_year = datetime.now().year
year_options = [str(y) for y in range(current_year, current_year - yearcount, -1)]

if 'select_all_years' not in st.session_state:
    st.session_state.select_all_years = False

if st.button("全选年份", key="all_years_btn"):
    st.session_state.select_all_years = not st.session_state.select_all_years

selected_years = []
cols_year = st.columns(yearcount)
for idx, year in enumerate(year_options):
    with cols_year[idx % yearcount]:
        if st.checkbox(year, key=f"year_{year}", value=st.session_state.select_all_years):
            selected_years.append(year)

# 输入关键词
st.markdown("### 输入关键词")
keywords = st.text_input("多个关键词请用英文逗号分隔：", "")

# 构造 conf+year 对应的URL映射
def build_conf_year_to_urls():
    mapping = {}
    for year in year_options:
        mapping[("OSDI", year)] = [f"https://dblp.org/db/conf/osdi/osdi{year}.html"]
        mapping[("ATC", year)] = [f"https://dblp.org/db/conf/usenix/usenix{year}.html"]
        mapping[("EuroSys", year)] = [f"https://dblp.org/db/conf/eurosys/eurosys{year}.html"]
        mapping[("ASPLOS", year)] = [
            f"https://dblp.org/db/conf/asplos/asplos{year}.html",
            f"https://dblp.org/db/conf/asplos/asplos{year}-1.html",
            f"https://dblp.org/db/conf/asplos/asplos{year}-2.html",
            f"https://dblp.org/db/conf/asplos/asplos{year}-3.html",
            f"https://dblp.org/db/conf/asplos/asplos{year}-4.html",
        ]
        mapping[("FAST", year)] = [f"https://dblp.org/db/conf/fast/fast{year}.html"]
        mapping[("SOSP", year)] = [f"https://dblp.org/db/conf/sosp/sosp{year}.html"]
        mapping[("ISCA", year)] = [f"https://dblp.org/db/conf/isca/isca{year}.html"]
        mapping[("SC", year)] = [f"https://dblp.org/db/conf/sc/sc{year}.html"]
        mapping[("HPCA", year)] = [f"https://dblp.org/db/conf/hpca/hpca{year}.html"]
        mapping[("DAC", year)] = [f"https://dblp.org/db/conf/dac/dac{year}.html"]
        mapping[("MICRO", year)] = [f"https://dblp.org/db/conf/micro/micro{year}.html"]
        mapping[("SIGCOMM", year)] = [f"https://dblp.org/db/conf/sigcomm/sigcomm{year}.html"]
        mapping[("MobiCom", year)] = [f"https://dblp.org/db/conf/mobicom/mobicom{year}.html"]
        mapping[("INFOCOM", year)] = [f"https://dblp.org/db/conf/infocom/infocom{year}.html"]
        mapping[("NSDI", year)] = [f"https://dblp.org/db/conf/nsdi/nsdi{year}.html"]
        mapping[("CoNEXT", year)] = [f"https://dblp.org/db/conf/conext/conext{year}.html"]
        mapping[("CCS", year)] = [f"https://dblp.org/db/conf/ccs/ccs{year}.html"]
        mapping[("S&P", year)] = [f"https://dblp.org/db/conf/sp/sp{year}.html"]
        mapping[("USENIX Security", year)] = [f"https://dblp.org/db/conf/uss/uss{year}.html"]
        mapping[("NDSS", year)] = [f"https://dblp.org/db/conf/ndss/ndss{year}.html"]
        mapping[("PPoPP", year)] = [f"https://dblp.org/db/conf/ppopp/ppopp{year}.html"]
    return mapping

conf_year_to_urls = build_conf_year_to_urls()

# 抓取单个页面
def fetch_papers_from_url(conf, year, url):
    papers = []
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        entries = soup.find_all('cite', class_='data')
        publs = soup.find_all('nav', class_='publ')

        for entry, publ in zip(entries, publs):
            title_tag = entry.find('span', class_='title')
            if not title_tag:
                continue
            title = title_tag.text.strip()

            title_lower = title.lower()
            if any(keyword in title_lower for keyword in ["symposium", "conference", "proceedings", "workshop"]) or conf.lower() in title_lower:
                continue

            paper_url = ""
            ee_li = publ.find('li', class_='ee')
            if ee_li:
                link = ee_li.find('a')
                if link and link.get('href'):
                    paper_url = link['href']

            authors = [a.text.strip() for a in entry.find_all('span', itemprop='author')]

            papers.append({
                "conference": conf,
                "year": year,
                "title": title,
                "authors": authors,
                "url": paper_url,
                "abstract": "NULL"
            })
    except Exception as e:
        st.error(f"❌ 抓取 {conf} {year} URL失败: {url}，错误：{e}")

    return papers

# 初始化 session_state
if 'raw_results' not in st.session_state:
    st.session_state.raw_results = []

if 'filtered_results' not in st.session_state:
    st.session_state.filtered_results = []

if 'last_selected_confs' not in st.session_state:
    st.session_state.last_selected_confs = []

if 'last_selected_years' not in st.session_state:
    st.session_state.last_selected_years = []

if 'last_keyword_input' not in st.session_state:
    st.session_state.last_keyword_input = ""

# ========== 主逻辑 ==========

trigger = st.button("🔍 抓取并筛选论文")

if trigger:
    if not selected_confs or not selected_years:
        st.warning("请至少选择一个会议和一个年份")
    else:
        keyword_list = [kw.strip().lower() for kw in keywords.split(",") if kw.strip()]
        st.session_state.last_keyword_input = keywords

        # 判断是否需要重新抓取
        if selected_confs != st.session_state.last_selected_confs or selected_years != st.session_state.last_selected_years:
            st.session_state.last_selected_confs = selected_confs
            st.session_state.last_selected_years = selected_years
            st.session_state.raw_results.clear()

            all_tasks = []
            for conf in selected_confs:
                for year in selected_years:
                    urls = conf_year_to_urls.get((conf, year))
                    if not urls:
                        st.error(f"未找到 {conf} {year} 的 URL，请补充到 conf_year_to_urls 中。")
                        continue
                    for url in urls:
                        all_tasks.append((conf, year, url))

            total_tasks = len(all_tasks)
            progress_bar = st.progress(0)
            with st.spinner("正在并发抓取论文..."):
                def task_wrapper(task):
                    conf, year, url = task
                    return fetch_papers_from_url(conf, year, url)

                total_results = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                    futures = {executor.submit(task_wrapper, task): task for task in all_tasks}
                    completed = 0
                    for future in concurrent.futures.as_completed(futures):
                        result = future.result()
                        total_results.extend(result)
                        completed += 1
                        progress_bar.progress(completed / total_tasks)

            st.session_state.raw_results = total_results
        else:
            st.info("会议和年份未变化，使用缓存的抓取结果")

        # 关键词筛选
        if st.session_state.raw_results:
            if keyword_list:
                st.session_state.filtered_results = [
                    paper for paper in st.session_state.raw_results
                    if any(kw in paper["title"].lower() for kw in keyword_list)
                ]
            else:
                st.session_state.filtered_results = st.session_state.raw_results
        else:
            st.warning("抓取失败或无论文数据")

# 显示结果
total = len(st.session_state.raw_results)
filtered = len(st.session_state.filtered_results)
st.success(f"总论文数：{total}，关键词筛选后剩余：{filtered}")
if st.session_state.filtered_results:
    # 下载按钮
    markdown_output = "# 论文列表\n\n"
    for idx, paper in enumerate(st.session_state.filtered_results, 1):
        authors = paper['authors']
        if len(authors) > 2:
            author_display = ', '.join(authors[:2]) + ", ... " + authors[-1]
        else:
            author_display = ', '.join(authors)

        markdown_output += f"## {idx}. {paper['title']}\n"
        markdown_output += f"- Conference: {paper['conference']} {paper['year']}\n"
        markdown_output += f"- Authors: {author_display}\n"
        markdown_output += f"- URL: [{paper['url']}]({paper['url']})\n\n"

    buffer = io.StringIO()
    buffer.write(markdown_output)
    buffer.seek(0)

    st.download_button(
        label="📄 下载筛选结果 (Markdown)",
        data=buffer.getvalue(),
        file_name="papers.md",
        mime="text/markdown"
    )

    # 展示每篇论文
    for idx, paper in enumerate(st.session_state.filtered_results, 1):
        authors = paper['authors']
        if len(authors) > 2:
            author_display = ', '.join(authors[:2]) + ", ... " + authors[-1]
        else:
            author_display = ', '.join(authors)

        st.markdown(
            f"""
            <div style="border:1px solid #ccc; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <strong style="font-size: 20px;">{idx}. {paper['title']}</strong><br>
                <span style="color: red;">{paper['conference']} {paper['year']}</span> by <span style="color: green;">[{author_display}]</span> from <a href="{paper['url']}">{paper['url']}</a><br>
            </div>
            """,
            unsafe_allow_html=True
        )