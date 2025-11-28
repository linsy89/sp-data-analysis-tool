"""
SP广告数据分析工具 - 数据处理模块

功能：
1. 从广告活动名称中提取维度（Parent Code, Pattern, Attribute）
2. 计算聚合指标（CTR, CPC, ROAS, ACoS, CVR, CPA等）
3. 支持单维度和交叉维度分析
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


def extract_parent_code(campaign_name: str) -> str:
    """
    从广告活动名称中提取 Parent Code（第一个空格前的内容）

    例: "SP-US 模式A1" -> "SP-US"
    """
    if not isinstance(campaign_name, str):
        return "未分类"

    parts = campaign_name.split()
    if len(parts) > 0 and parts[0].strip():
        return parts[0]
    return "未分类"


def extract_pattern(campaign_name: str) -> str:
    """
    从广告活动名称中提取 Pattern（第一个和第二个空格之间的内容）

    例: "SP-US 模式A1" -> "模式A1"
    """
    if not isinstance(campaign_name, str):
        return "未分类"

    parts = campaign_name.split()
    if len(parts) > 1 and parts[1].strip():
        return parts[1]
    return "未分类"


def extract_attribute(campaign_name: str) -> str:
    """
    从广告活动名称中提取 Attribute（第一个空格之后的第一个单词）

    例: "SP-US 模式A1 品类B" -> "品类B"
    例: "SP-US 模式A1" -> "未分类"
    """
    if not isinstance(campaign_name, str):
        return "未分类"

    parts = campaign_name.split()
    if len(parts) > 2 and parts[2].strip():
        return parts[2]
    return "未分类"


def extract_all_dimensions(df: pd.DataFrame) -> pd.DataFrame:
    """
    为数据框添加三个维度列：Parent Code, Pattern, Attribute

    参数:
        df: 原始数据框，应包含 Campaign Name 或 广告活动 列

    返回:
        包含新维度列的数据框
    """
    df_copy = df.copy()

    # 确定广告活动列名（支持中英文）
    campaign_col = None
    if 'Campaign Name' in df_copy.columns:
        campaign_col = 'Campaign Name'
    elif '广告活动' in df_copy.columns:
        campaign_col = '广告活动'
    else:
        raise ValueError("数据框中未找到 'Campaign Name' 或 '广告活动' 列")

    # 提取维度
    df_copy['Parent Code'] = df_copy[campaign_col].apply(extract_parent_code)
    df_copy['Pattern'] = df_copy[campaign_col].apply(extract_pattern)
    df_copy['Attribute'] = df_copy[campaign_col].apply(extract_attribute)

    return df_copy


def get_dimension_summary(df: pd.DataFrame) -> Dict[str, int]:
    """
    获取维度的统计摘要

    参数:
        df: 包含维度列的数据框

    返回:
        包含各维度唯一值个数的字典
    """
    summary = {
        'parent_code_count': df['Parent Code'].nunique(),
        'pattern_count': df['Pattern'].nunique(),
        'attribute_count': df['Attribute'].nunique(),
    }
    return summary


def format_value(value: float, metric_type: str) -> str:
    """
    格式化指标值

    参数:
        value: 数值
        metric_type: 指标类型 ('percent', 'currency', 'ratio', 'number')

    返回:
        格式化后的字符串
    """
    if pd.isna(value) or value is None:
        return "-"

    try:
        value = float(value)
    except (ValueError, TypeError):
        return "-"

    if metric_type == 'percent':
        return f"{value:.2f}%"
    elif metric_type == 'currency':
        return f"¥{value:.2f}"
    elif metric_type == 'ratio':
        return f"{value:.2f}x"
    elif metric_type == 'number':
        return f"{int(value)}"
    else:
        return str(value)


def aggregate_single(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """
    按单个维度进行聚合分析

    参数:
        df: 包含维度列的数据框
        dimension: 维度名称 ('Parent Code', 'Pattern', 'Attribute')

    返回:
        聚合结果数据框
    """

    # 验证维度
    if dimension not in ['Parent Code', 'Pattern', 'Attribute']:
        raise ValueError(f"无效的维度: {dimension}")

    # 需要求和的列
    sum_columns = {
        col: 'sum' for col in df.columns
        if col not in ['Campaign Name', 'Parent Code', 'Pattern', 'Attribute']
    }

    # 执行分组和求和
    result = df.groupby(dimension).agg(sum_columns).reset_index()

    # 计算派生指标（需要原始数据中有特定列）
    # 确定关键列名称（可能有不同的变体）

    # 定义可能的列名映射
    column_mappings = {
        'impressions': ['Impressions', '曝光量', '展示'],
        'click': ['Clicks', 'Click', '点击', '点击数'],
        'spend': ['Spend', 'Spend ($)', '花费', '支出'],
        'sales': ['Sales', '销售额', '销售'],
        'conversions': ['Conversions', '转化', '转化数']
    }

    # 找到实际存在的列
    actual_columns = {}
    for key, possible_names in column_mappings.items():
        for col_name in possible_names:
            if col_name in result.columns:
                actual_columns[key] = col_name
                break

    # 计算 CTR（点击率）= (点击 / 曝光) × 100
    if 'click' in actual_columns and 'impressions' in actual_columns:
        click_col = actual_columns['click']
        imp_col = actual_columns['impressions']
        result['CTR'] = (result[click_col] / result[imp_col] * 100).apply(
            lambda x: format_value(x, 'percent') if pd.notna(x) else "-"
        )

    # 计算 CPC（单次点击成本）= 花费 / 点击
    if 'spend' in actual_columns and 'click' in actual_columns:
        spend_col = actual_columns['spend']
        click_col = actual_columns['click']
        result['CPC'] = (result[spend_col] / result[click_col]).apply(
            lambda x: format_value(x, 'currency') if pd.notna(x) else "-"
        )

    # 计算 ROAS（广告支出回报率）= 销售额 / 花费
    if 'sales' in actual_columns and 'spend' in actual_columns:
        sales_col = actual_columns['sales']
        spend_col = actual_columns['spend']
        result['ROAS'] = (result[sales_col] / result[spend_col]).apply(
            lambda x: format_value(x, 'ratio') if pd.notna(x) else "-"
        )

    # 计算 ACoS（广告成本占比）= (花费 / 销售额) × 100
    if 'spend' in actual_columns and 'sales' in actual_columns:
        spend_col = actual_columns['spend']
        sales_col = actual_columns['sales']
        result['ACoS'] = (result[spend_col] / result[sales_col] * 100).apply(
            lambda x: format_value(x, 'percent') if pd.notna(x) else "-"
        )

    # 计算 CVR（转化率）= (转化 / 点击) × 100
    if 'conversions' in actual_columns and 'click' in actual_columns:
        conv_col = actual_columns['conversions']
        click_col = actual_columns['click']
        result['CVR'] = (result[conv_col] / result[click_col] * 100).apply(
            lambda x: format_value(x, 'percent') if pd.notna(x) else "-"
        )

    # 计算 CPA（单次转化成本）= 花费 / 转化
    if 'spend' in actual_columns and 'conversions' in actual_columns:
        spend_col = actual_columns['spend']
        conv_col = actual_columns['conversions']
        result['CPA'] = (result[spend_col] / result[conv_col]).apply(
            lambda x: format_value(x, 'currency') if pd.notna(x) else "-"
        )

    # 重新排列列，确保维度列在第一列
    cols = [dimension]
    cols.extend([col for col in result.columns if col != dimension])
    result = result[cols]

    # 排序
    result = result.sort_values(by=dimension).reset_index(drop=True)

    return result


def aggregate_cross(df: pd.DataFrame, dim1: str, dim2: str) -> pd.DataFrame:
    """
    按两个维度进行交叉聚合分析

    参数:
        df: 包含维度列的数据框
        dim1: 第一个维度
        dim2: 第二个维度

    返回:
        交叉聚合结果数据框
    """

    # 验证维度
    valid_dims = ['Parent Code', 'Pattern', 'Attribute']
    if dim1 not in valid_dims or dim2 not in valid_dims:
        raise ValueError(f"无效的维度，应该是 {valid_dims} 中的一个")

    if dim1 == dim2:
        raise ValueError("两个维度不能相同")

    # 需要求和的列
    sum_columns = {
        col: 'sum' for col in df.columns
        if col not in ['Campaign Name', 'Parent Code', 'Pattern', 'Attribute']
    }

    # 执行分组和求和
    result = df.groupby([dim1, dim2]).agg(sum_columns).reset_index()

    # 按第一个维度排序
    result = result.sort_values(by=[dim1, dim2]).reset_index(drop=True)

    return result


# 数据验证函数
def validate_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    验证数据框是否符合预期格式

    参数:
        df: 待验证的数据框

    返回:
        (是否有效, 错误消息列表)
    """
    errors = []

    # 检查必要的列
    if 'Campaign Name' not in df.columns:
        errors.append("缺少 'Campaign Name' 列")

    # 检查数据类型
    if df.empty:
        errors.append("数据框为空")

    return len(errors) == 0, errors
