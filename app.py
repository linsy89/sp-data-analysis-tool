import streamlit as st
import pandas as pd
import pickle
from pathlib import Path
from data_processor import (
    extract_all_dimensions,
    get_dimension_summary,
    aggregate_single,
    aggregate_cross,
)

# 页面配置
st.set_page_config(
    page_title="SP广告数据分析工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS for styling
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #0066cc;
    }
    .metric-label {
        font-size: 12px;
        color: #555;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 缓存管理
CACHE_DIR = Path(".streamlit_cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_FILE = CACHE_DIR / "df_extracted.pkl"

def save_df_cache(df):
    """保存提取后的数据到文件"""
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(df, f)
    except Exception as e:
        st.warning(f"⚠️ 数据缓存保存失败: {str(e)}")

def load_df_cache():
    """从文件加载提取后的数据"""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        st.warning(f"⚠️ 数据缓存加载失败: {str(e)}")
    return None

def clear_df_cache():
    """清除缓存文件"""
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
    except Exception as e:
        st.warning(f"⚠️ 缓存清除失败: {str(e)}")

# 初始化 session state
if 'df' not in st.session_state:
    st.session_state.df = None
    st.session_state.file_name = None
    st.session_state.df_extracted = None
    st.session_state.summary = None

# 详情页面处理
def show_detail_page(dimension, value):
    """显示特定维度值的详情页面"""
    st.title(f"📊 {dimension} 详情页")
    st.markdown(f"### {dimension}: **{value}**")

    # 从缓存加载数据
    df_extracted = load_df_cache()
    if df_extracted is None:
        st.error("❌ 无法加载数据，请返回主页面重新上传文件")
        return

    # 过滤数据
    df_filtered = df_extracted[df_extracted[dimension] == value]

    if df_filtered.empty:
        st.warning(f"⚠️ 未找到 {dimension}='{value}' 的数据")
        return

    # 显示该维度值的聚合总结
    summary_data = aggregate_single(df_filtered, dimension)

    if not summary_data.empty:
        st.markdown("### 📈 汇总数据")
        st.dataframe(
            summary_data,
            use_container_width=True,
            hide_index=True,
        )

    # 显示原始数据
    st.markdown("### 📋 详细数据")

    # 移除 Parent Code 和 Pattern 列（如果存在）以简化显示
    display_cols = [col for col in df_filtered.columns
                   if col not in ['Parent Code', 'Pattern']]
    st.dataframe(
        df_filtered[display_cols],
        use_container_width=True,
        hide_index=True,
    )

    # 返回链接
    st.markdown("---")
    if st.button("← 返回主页面"):
        st.query_params.clear()
        st.rerun()

# 检查是否在详情页
query_params = st.query_params
if 'dimension' in query_params and 'value' in query_params:
    show_detail_page(query_params['dimension'], query_params['value'])
    st.stop()

# ============ 主页面 ============

st.title("📊 SP广告数据分析工具")
st.markdown("---")

# 侧边栏 - 文件上传
st.sidebar.header("📁 文件上传")
uploaded_file = st.sidebar.file_uploader(
    "上传 Excel 文件",
    type=['xlsx'],
    help="请上传包含广告数据的 Excel 文件"
)

if uploaded_file is not None:
    # 【关键修复】检测是否是新文件，如果是则清除旧缓存
    if st.session_state.file_name != uploaded_file.name:
        st.session_state.file_name = uploaded_file.name
        st.session_state.df = None
        st.session_state.df_extracted = None
        st.session_state.summary = None
        clear_df_cache()  # 清除旧缓存
        st.sidebar.info("✅ 检测到新文件，已清除旧缓存")

    # 读取 Excel 文件
    try:
        df = pd.read_excel(uploaded_file)
        st.session_state.df = df

        # 显示文件信息
        with st.sidebar.expander("📊 文件信息"):
            st.write(f"**文件名**: {uploaded_file.name}")
            st.write(f"**行数**: {len(df)}")
            st.write(f"**列数**: {len(df.columns)}")
            st.write(f"**列名**: {', '.join(df.columns)}")

    except Exception as e:
        st.error(f"❌ 文件读取失败: {str(e)}")
        st.stop()

    # 数据提取
    if st.session_state.df_extracted is None:
        with st.spinner("⏳ 正在提取维度..."):
            try:
                df_extracted = extract_all_dimensions(st.session_state.df)
                st.session_state.df_extracted = df_extracted
                st.session_state.summary = get_dimension_summary(df_extracted)

                # 保存到缓存文件，以便详情页可以访问
                save_df_cache(df_extracted)

            except Exception as e:
                st.error(f"❌ 维度提取失败: {str(e)}")
                st.stop()

        st.success("✅ 维度提取完成")

    # 显示原始数据预览
    with st.expander("📋 原始数据预览", expanded=False):
        st.dataframe(st.session_state.df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 显示维度提取结果
    st.markdown("### 🔍 维度提取结果")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Parent Code 个数", st.session_state.summary['parent_code_count'])
    with col2:
        st.metric("Pattern 个数", st.session_state.summary['pattern_count'])
    with col3:
        st.metric("Attribute 个数", st.session_state.summary['attribute_count'])

    # 显示提取后的数据
    with st.expander("📄 提取后的数据", expanded=False):
        st.dataframe(
            st.session_state.df_extracted,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    # ============ 步骤2：单维度分析 ============
    st.markdown("### 📊 步骤2：单维度分析")

    # 选择维度
    dimension = st.selectbox(
        "选择分析维度",
        ["Parent Code", "Pattern", "Attribute"],
        help="选择要分析的维度"
    )

    if st.button("🔍 执行分析"):
        with st.spinner(f"⏳ 正在分析 {dimension}..."):
            try:
                result = aggregate_single(st.session_state.df_extracted, dimension)

                if result.empty:
                    st.warning(f"⚠️ 未找到 {dimension} 的分析结果")
                else:
                    st.success("✅ 分析完成")

                    # 显示结果表格
                    st.markdown(f"#### {dimension} 分析结果")

                    # 【重要】转换为 HTML 表格，在第一列显示超链接
                    df_display = result.copy()
                    dimension_col = df_display.columns[0]

                    # 生成 HTML 表格，第一列为超链接
                    def make_clickable(value):
                        # 确保 value 是字符串类型
                        value_str = str(value)
                        return f'<a href="?dimension={dimension}&value={value_str}" target="_blank">{value_str}</a>'

                    df_display[dimension_col] = df_display[dimension_col].apply(make_clickable)

                    # 转换为 HTML 并显示
                    html_table = df_display.to_html(escape=False, index=False)
                    st.markdown(html_table, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ 分析失败: {str(e)}")

else:
    st.info("👈 请在左侧栏上传 Excel 文件以开始分析")

# 底部信息
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
    <p>📊 SP广告数据分析工具 v1.0 | 💡 如有问题，请重新上传文件</p>
    </div>
    """,
    unsafe_allow_html=True,
)
