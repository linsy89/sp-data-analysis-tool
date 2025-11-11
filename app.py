"""
SP广告数据分析工具 - Streamlit Web应用

功能：
  - Excel文件上传和数据提取
  - 维度统计展示
  - 单维度和交叉分析
  - 结果导出

使用方式：
  streamlit run app.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from data_processor import (
    extract_all_dimensions,
    validate_excel,
    get_dimension_summary,
    aggregate_single
)

# ============================================================================
# 页面配置
# ============================================================================

st.set_page_config(
    page_title="SP广告数据分析工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .section-header {
        font-size: 1.3rem;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# 初始化Session State
# ============================================================================

if 'df' not in st.session_state:
    st.session_state.df = None
    st.session_state.df_extracted = None
    st.session_state.summary = None
    st.session_state.file_name = None

# ============================================================================
# 页面路由 - 检查是否为详情页
# ============================================================================

def show_detail_page():
    """显示维度值详情页"""
    # 获取URL参数
    dimension = st.query_params.get('dimension', '')
    value = st.query_params.get('value', '')

    if not dimension or not value:
        st.error("❌ 无效的详情页链接")
        return

    # 维度显示名称
    dimension_names = {
        'parent_code': 'Parent Code',
        'pattern': '图案',
        'attribute': '属性'
    }

    df_extracted = st.session_state.df_extracted

    # 返回按钮
    col1, col2 = st.columns([1, 9])
    with col1:
        if st.button("← 返回分析"):
            st.query_params.clear()
            st.rerun()

    # 标题
    st.markdown(f"## 📊 {dimension_names.get(dimension, dimension)}详情：{value}")
    st.markdown("---")

    # 1. 汇总统计
    st.markdown("### 📈 汇总统计")
    try:
        aggregated = aggregate_single(df_extracted, dimension)
        single_row = aggregated[aggregated[dimension] == value]

        if len(single_row) > 0:
            # 显示汇总数据
            st.dataframe(
                single_row,
                use_container_width=True,
                hide_index=True
            )

            # 显示关键指标
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                if '数据行数' in single_row.columns:
                    st.metric("数据行数", int(single_row['数据行数'].iloc[0]))
            with metric_col2:
                if '花费' in single_row.columns:
                    st.metric("总花费", f"¥{single_row['花费'].iloc[0]:,.2f}")
            with metric_col3:
                if '销售额' in single_row.columns:
                    st.metric("总销售额", f"¥{single_row['销售额'].iloc[0]:,.2f}")
        else:
            st.warning(f"⚠️ 未找到 {dimension_names.get(dimension, dimension)} = '{value}' 的数据")
            return

    except Exception as e:
        st.error(f"❌ 汇总统计出错：{str(e)}")
        return

    # 2. 明细数据
    st.markdown("---")
    st.markdown("### 📋 明细数据")

    try:
        detail_data = df_extracted[df_extracted[dimension] == value].copy()

        if len(detail_data) > 0:
            # 重命名列以更好的显示
            display_cols = [col for col in detail_data.columns if col not in ['is_valid']]
            detail_display = detail_data[display_cols].copy()

            st.dataframe(
                detail_display,
                use_container_width=True,
                hide_index=True
            )

            st.info(f"📊 共 {len(detail_data)} 行数据")
        else:
            st.warning(f"⚠️ 未找到明细数据")

    except Exception as e:
        st.error(f"❌ 明细数据加载出错：{str(e)}")


# 检查是否为详情页请求
if 'dimension' in st.query_params and 'value' in st.query_params:
    if st.session_state.df_extracted is not None:
        show_detail_page()
        st.stop()
    else:
        st.error("❌ 请先上传数据文件")


# ============================================================================
# 侧边栏 - 文件上传
# ============================================================================

with st.sidebar:
    st.markdown("## 📂 数据上传")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "选择Excel文件",
        type=['xlsx', 'xls'],
        help="支持 .xlsx 和 .xls 格式的Excel文件"
    )

    if uploaded_file is not None:
        try:
            # 读取Excel文件
            df = pd.read_excel(uploaded_file)

            st.session_state.file_name = uploaded_file.name

            # 验证数据
            validation = validate_excel(df)

            if validation['valid']:
                st.success("✅ 文件读取成功")

                # 显示文件基本信息
                st.info(f"""
                📊 文件信息：
                - 行数：{len(df)}
                - 列数：{len(df.columns)}
                """)

                # 保存到session_state
                st.session_state.df = df

                # 如果还没有提取过，进行提取
                if st.session_state.df_extracted is None:
                    with st.spinner("⏳ 正在提取维度..."):
                        df_extracted = extract_all_dimensions(df)
                        st.session_state.df_extracted = df_extracted
                        st.session_state.summary = get_dimension_summary(df_extracted)

                    st.success("✅ 维度提取完成")
            else:
                st.error("❌ 数据验证失败")
                for error in validation['errors']:
                    st.error(f"  - {error}")
                st.stop()

        except Exception as e:
            st.error(f"❌ 文件读取出错：{str(e)}")
            st.stop()
    else:
        st.info("👈 请先上传Excel文件")


# ============================================================================
# 主区域 - 标题和说明
# ============================================================================

st.markdown("# 📊 SP广告数据分析工具")
st.markdown("""
这是一个为SP广告数据进行维度提取和多维度分析的工具。
可以快速提取广告活动名称中的关键信息，进行单维度和交叉分析。
""")

st.markdown("---")

# ============================================================================
# 主区域 - 数据提取结果展示
# ============================================================================

if st.session_state.df is not None and st.session_state.df_extracted is not None:

    summary = st.session_state.summary
    df_extracted = st.session_state.df_extracted

    # 标题
    st.markdown("## 📈 数据提取结果")

    # 四个指标卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="总数据行数",
            value=summary['total_rows'],
            delta=None
        )

    with col2:
        st.metric(
            label="Parent Code",
            value=f"{summary['parent_codes']['count']} 种",
            delta=None
        )

    with col3:
        st.metric(
            label="图案",
            value=f"{summary['patterns']['count']} 种",
            delta=None
        )

    with col4:
        st.metric(
            label="属性",
            value=f"{summary['attributes']['count']} 种",
            delta=None
        )

    st.markdown("---")

    # 数据质量信息
    col1, col2 = st.columns(2)

    with col1:
        valid_count = summary['total_rows'] - summary['invalid_count']
        valid_pct = 100 * valid_count / summary['total_rows']

        st.success(f"""
        ✅ **有效数据**：{valid_count} 行 ({valid_pct:.1f}%)
        """)

    with col2:
        if summary['invalid_count'] > 0:
            invalid_pct = 100 * summary['invalid_count'] / summary['total_rows']
            st.warning(f"""
            ⚠️ **异常数据**：{summary['invalid_count']} 行 ({invalid_pct:.1f}%)
            """)
        else:
            st.success("✅ **无异常数据**")

    # ========================================================================
    # 维度详情 - 可展开
    # ========================================================================

    st.markdown("---")
    st.markdown("## 📋 维度详情")

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.expander(f"📍 Parent Code（{summary['parent_codes']['count']}种）", expanded=False):
            parent_codes_list = sorted(summary['parent_codes']['values'])
            for i, code in enumerate(parent_codes_list, 1):
                st.write(f"{i}. {code}")

    with col2:
        with st.expander(f"🎨 图案（{summary['patterns']['count']}种）", expanded=False):
            patterns_list = sorted(summary['patterns']['values'])
            for i, pattern in enumerate(patterns_list, 1):
                st.write(f"{i}. {pattern}")

    with col3:
        with st.expander(f"🏷️ 属性（{summary['attributes']['count']}种）", expanded=False):
            attributes_list = sorted(summary['attributes']['values'])
            for i, attr in enumerate(attributes_list, 1):
                st.write(f"{i}. {attr}")

    # ========================================================================
    # 样本数据展示
    # ========================================================================

    st.markdown("---")
    st.markdown("## 📊 样本数据（前10行）")

    sample_cols = ['广告活动', 'parent_code', 'pattern', 'attribute', 'is_valid']
    sample_data = df_extracted[sample_cols].head(10).copy()

    # 重命名列以更好的显示
    sample_data.columns = ['原始广告活动', 'Parent Code', '图案', '属性', '有效']

    st.dataframe(
        sample_data,
        use_container_width=True,
        hide_index=True
    )

    # ========================================================================
    # 异常数据展示（如果有）
    # ========================================================================

    if summary['invalid_count'] > 0:
        st.markdown("---")
        st.markdown("## ⚠️ 异常数据详情")

        invalid_data = df_extracted[~df_extracted['is_valid']]
        invalid_cols = ['广告活动', 'parent_code', 'pattern', 'attribute']
        invalid_display = invalid_data[invalid_cols].copy()
        invalid_display.columns = ['原始广告活动', 'Parent Code', '图案', '属性']

        st.warning(f"共 {len(invalid_data)} 行异常数据：")
        st.dataframe(
            invalid_display,
            use_container_width=True,
            hide_index=True
        )

    # ========================================================================
    # Step 2：单维度分析
    # ========================================================================

    st.markdown("---")
    st.markdown("## 📊 Step 2：单维度分析")

    col1, col2 = st.columns([3, 1])

    with col1:
        dimension = st.selectbox(
            "选择要分析的维度",
            options=["parent_code", "pattern", "attribute"],
            format_func=lambda x: {
                "parent_code": "📍 Parent Code",
                "pattern": "🎨 图案",
                "attribute": "🏷️ 属性"
            }[x]
        )

    with col2:
        st.write("")  # 占位符用于对齐
        analyze_button = st.button("🔍 分析", key="step2_analyze", use_container_width=True)

    if analyze_button:
        try:
            with st.spinner(f"⏳ 正在按 {['Parent Code', '图案', '属性'][['parent_code', 'pattern', 'attribute'].index(dimension)]} 进行聚合分析..."):
                result = aggregate_single(df_extracted, dimension)

                # 按花费降序排列
                if '花费' in result.columns:
                    result = result.sort_values(by='花费', ascending=False, na_position='last').reset_index(drop=True)

            st.success("✅ 分析完成")

            # 生成可点击的结果表格（维度列添加链接）
            result_display = result.copy()
            dimension_col = result_display.columns[0]  # 第一列是维度列

            # 创建链接HTML
            def create_detail_link(value):
                """创建跳转链接，在新窗口打开详情页"""
                return f'<a href="?dimension={dimension}&value={value}" target="_blank" style="color: #1f77b4; text-decoration: underline;">{value}</a>'

            result_display[dimension_col] = result_display[dimension_col].apply(create_detail_link)

            # 使用HTML渲染表格
            html_table = result_display.to_html(escape=False, index=False)
            st.markdown(html_table, unsafe_allow_html=True)

            # 显示摘要统计
            st.markdown("#### 📈 汇总统计")
            summary_col1, summary_col2, summary_col3 = st.columns(3)

            with summary_col1:
                st.metric(
                    label="维度值个数",
                    value=len(result)
                )

            with summary_col2:
                if '数据行数' in result.columns:
                    total_rows = result['数据行数'].sum()
                    st.metric(
                        label="总数据行数",
                        value=int(total_rows)
                    )

            with summary_col3:
                if '花费' in result.columns:
                    total_spend = result['花费'].sum()
                    st.metric(
                        label="总花费",
                        value=f"¥{total_spend:,.2f}"
                    )

        except Exception as e:
            st.error(f"❌ 分析出错：{str(e)}")

    # ========================================================================
    # 底部说明
    # ========================================================================

    st.markdown("---")
    st.markdown("""
    ### 💡 下一步操作

    ✅ 数据提取完成！接下来你可以：
    - 进行**单维度分析**：选择某个维度查看聚合结果
    - 进行**交叉分析**：选择两个维度进行交叉透视
    - 对数据进行**筛选**：按特定条件过滤数据
    - **导出结果**：将分析结果保存为Excel

    > 提示：在页面左侧可以上传新的文件重新分析
    """)

else:
    # 未上传文件时的提示
    st.info("""
    👈 **请在左侧侧边栏上传Excel文件开始分析**

    支持的文件格式：
    - .xlsx（推荐）
    - .xls

    上传后会自动：
    1. 读取文件内容
    2. 提取广告活动名称中的维度信息
    3. 显示统计结果和样本数据
    """)

    # 显示文件格式说明
    st.markdown("---")
    st.markdown("### 📝 文件格式要求")
    st.markdown("""
    Excel文件必须包含以下列：
    - **广告活动列**（C列）：包含形如"City-LightballsCollage-IP15 aesthetic"的数据
    - **数值列**（可选）：花费、销售额、ROAS等指标

    广告活动名称格式：
    - **Parent Code**：第一个"-"之前的内容（如：City）
    - **图案**：第一个"-"和第二个"-"之间的内容（如：LightballsCollage）
    - **属性**：第一个空格之后的第一个单词（如：aesthetic）

    示例：
    ```
    City-LightballsCollage-IP15 aesthetic
    ↓ 提取 ↓
    Parent Code: City
    图案: LightballsCollage
    属性: aesthetic
    ```
    """)
