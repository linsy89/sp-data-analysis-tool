"""
SP广告数据分析工具 - 数据处理核心模块

提供数据提取、验证、聚合等核心功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


def extract_dimensions(campaign_name: str) -> Dict:
    """
    从广告活动名称提取3个维度

    参数:
        campaign_name (str): 广告活动名称，格式如 "City-LightballsCollage-IP15 aesthetic"

    返回:
        dict: {
            'parent_code': str,      # 第一个"-"之前的内容
            'pattern': str,          # 第一个"-"和第二个"-"之间的内容
            'attribute': str,        # 第一个空格之后的内容
            'is_valid': bool         # 是否有效（至少有一个维度被成功提取）
        }

    示例:
        >>> extract_dimensions("City-LightballsCollage-IP15 aesthetic")
        {
            'parent_code': 'City',
            'pattern': 'LightballsCollage',
            'attribute': 'aesthetic',
            'is_valid': True
        }

        >>> extract_dimensions("NoHyphen aesthetic")
        {
            'parent_code': '未分类',
            'pattern': '未分类',
            'attribute': 'aesthetic',
            'is_valid': True
        }
    """
    # 处理None和非字符串输入
    if campaign_name is None or not isinstance(campaign_name, str):
        return {
            'parent_code': '未分类',
            'pattern': '未分类',
            'attribute': '未分类',
            'is_valid': False
        }

    # 处理空字符串
    campaign_name = campaign_name.strip()
    if not campaign_name:
        return {
            'parent_code': '未分类',
            'pattern': '未分类',
            'attribute': '未分类',
            'is_valid': False
        }

    # 提取Parent Code（第一个"-"之前的内容）
    if '-' in campaign_name:
        parts = campaign_name.split('-')
        parent_code = parts[0].strip()

        # 提取图案（第一个"-"和第二个"-"之间的内容）
        if len(parts) >= 2:
            pattern = parts[1].strip()
            # 如果pattern为空（如"City-"），标记为未分类
            if not pattern:
                pattern = '未分类'
        else:
            pattern = '未分类'
    else:
        parent_code = '未分类'
        pattern = '未分类'

    # 提取属性（第一个空格之后的第一个单词）
    if ' ' in campaign_name:
        # 分割所有单词
        words = campaign_name.split(' ')
        # 取第一个空格之后的第一个单词（即index=1）
        attribute = words[1].strip() if len(words) > 1 else '未分类'
    else:
        attribute = '未分类'

    # 确保属性不是空值
    if not attribute or attribute.strip() == '':
        attribute = '未分类'

    # 判断是否有效（至少提取了一个维度）
    is_valid = (
        parent_code != '未分类' or
        pattern != '未分类' or
        attribute != '未分类'
    )

    return {
        'parent_code': parent_code,
        'pattern': pattern,
        'attribute': attribute,
        'is_valid': is_valid
    }


def extract_all_dimensions(df: pd.DataFrame) -> pd.DataFrame:
    """
    对整个DataFrame提取所有维度

    对"广告活动"列的每一行调用extract_dimensions()，
    并将结果添加为4列新字段到DataFrame中。

    参数:
        df (pd.DataFrame): 原始DataFrame，必须包含"广告活动"列

    返回:
        pd.DataFrame: 扩展后的DataFrame，新增4列：
            - parent_code: Parent Code维度
            - pattern: 图案维度
            - attribute: 属性维度
            - is_valid: 是否有效的标记

    异常:
        KeyError: 如果DataFrame中不存在"广告活动"列
    """
    if '广告活动' not in df.columns:
        raise KeyError('DataFrame必须包含"广告活动"列')

    df = df.copy()

    # 对每一行提取维度
    extracted = df['广告活动'].apply(extract_dimensions)

    # 将提取结果转换为DataFrame
    extracted_df = pd.DataFrame(extracted.tolist())

    # 合并原始DataFrame和提取结果
    df = pd.concat([df, extracted_df], axis=1)

    # 如果是空DataFrame，确保新列存在
    if len(df) == 0:
        for col in ['parent_code', 'pattern', 'attribute', 'is_valid']:
            if col not in df.columns:
                df[col] = pd.Series(dtype='object')
    else:
        # 确保维度列中没有空值，用"未分类"替换
        for col in ['parent_code', 'pattern', 'attribute']:
            if col in df.columns:
                df[col] = df[col].fillna('未分类')
                df[col] = df[col].replace('', '未分类')

    return df


def validate_excel(df: pd.DataFrame) -> Dict:
    """
    验证Excel数据有效性

    检查数据的完整性和关键列的存在性

    参数:
        df (pd.DataFrame): 需要验证的DataFrame

    返回:
        dict: {
            'valid': bool,           # 是否通过验证
            'errors': list[str],     # 错误信息列表
            'warnings': list[str]    # 警告信息列表
        }
    """
    errors = []
    warnings = []

    # 检查关键列：广告活动
    if '广告活动' not in df.columns:
        errors.append("缺少必需列'广告活动'（C列）")

    # 检查数据行数
    if len(df) == 0:
        errors.append("Excel数据为空")

    # 检查关键数值列
    numeric_cols_check = ['花费', '销售额']
    for col in numeric_cols_check:
        if col not in df.columns:
            warnings.append(f"缺少数值列'{col}'，部分功能可能不可用")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def aggregate_single(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """
    按单个维度聚合所有数值列

    参数:
        df (pd.DataFrame): 包含原始数据和提取维度的DataFrame
        dimension (str): 聚合维度，可选值：
            - 'parent_code': 按Parent Code聚合
            - 'pattern': 按图案聚合
            - 'attribute': 按属性聚合

    返回:
        pd.DataFrame: 聚合后的结果，包含维度列和所有聚合的数值列

    异常:
        ValueError: 如果dimension参数无效
    """
    valid_dimensions = ['parent_code', 'pattern', 'attribute']
    if dimension not in valid_dimensions:
        raise ValueError(f"dimension必须是以下之一：{valid_dimensions}")

    if dimension not in df.columns:
        raise ValueError(f"DataFrame中不存在列'{dimension}'")

    # 为了避免文本值导致的错误，先转换为数值类型（非数值的会变成NaN）
    df_copy = df.copy()

    # 需要求和的列
    sum_cols = [
        '花费', '销售额', '直接成交销售额', '广告订单', '直接成交订单',
        '曝光量', '点击', '广告笔单价', '广告销量'
    ]

    # 需要计算的比率列（不能直接求和）
    ratio_cols = ['CPC', 'CTR', 'ACoS', 'ROAS', 'CPA', 'CVR']

    # 只保留数据框中存在的列
    existing_sum_cols = [col for col in sum_cols if col in df_copy.columns]
    existing_ratio_cols = [col for col in ratio_cols if col in df_copy.columns]

    # 转换为数值类型
    for col in existing_sum_cols + existing_ratio_cols:
        df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')

    # 按维度分组，计算求和列
    agg_dict = {col: 'sum' for col in existing_sum_cols}
    result = df_copy.groupby(dimension, as_index=False).agg(agg_dict)

    # 添加"数据行数"列
    row_counts = df_copy.groupby(dimension, as_index=False).size()
    row_counts.rename(columns={'size': '数据行数'}, inplace=True)
    result = result.merge(row_counts, on=dimension)

    # 计算比率列（需要重新计算）
    # CTR = 点击 / 曝光量 * 100 (显示为百分比)
    if 'CTR' in existing_ratio_cols and '点击' in existing_sum_cols and '曝光量' in existing_sum_cols:
        ctr_values = (result['点击'] / result['曝光量'] * 100).round(2)
        ctr_values = ctr_values.replace([np.inf, -np.inf], np.nan)
        result['CTR'] = ctr_values.apply(lambda x: f"{x}%" if pd.notna(x) else "")

    # CPC = 花费 / 点击 (显示为¥)
    if 'CPC' in existing_ratio_cols and '花费' in existing_sum_cols and '点击' in existing_sum_cols:
        cpc_values = (result['花费'] / result['点击']).round(2)
        cpc_values = cpc_values.replace([np.inf, -np.inf], np.nan)
        result['CPC'] = cpc_values.apply(lambda x: f"¥{x}" if pd.notna(x) else "")

    # ROAS = 销售额 / 花费 (显示为倍数)
    if 'ROAS' in existing_ratio_cols and '销售额' in existing_sum_cols and '花费' in existing_sum_cols:
        roas_values = (result['销售额'] / result['花费']).round(2)
        roas_values = roas_values.replace([np.inf, -np.inf], np.nan)
        result['ROAS'] = roas_values.apply(lambda x: f"{x}x" if pd.notna(x) else "")

    # ACoS = 花费 / 销售额 * 100 (显示为百分比)
    if 'ACoS' in existing_ratio_cols and '花费' in existing_sum_cols and '销售额' in existing_sum_cols:
        acos_values = (result['花费'] / result['销售额'] * 100).round(2)
        acos_values = acos_values.replace([np.inf, -np.inf], np.nan)
        result['ACoS'] = acos_values.apply(lambda x: f"{x}%" if pd.notna(x) else "")

    # CVR = 直接成交订单 / 点击 * 100 (显示为百分比)
    if 'CVR' in existing_ratio_cols and '直接成交订单' in existing_sum_cols and '点击' in existing_sum_cols:
        cvr_values = (result['直接成交订单'] / result['点击'] * 100).round(2)
        cvr_values = cvr_values.replace([np.inf, -np.inf], np.nan)
        result['CVR'] = cvr_values.apply(lambda x: f"{x}%" if pd.notna(x) else "")

    # CPA = 花费 / 直接成交订单 (显示为¥)
    if 'CPA' in existing_ratio_cols and '花费' in existing_sum_cols and '直接成交订单' in existing_sum_cols:
        cpa_values = (result['花费'] / result['直接成交订单']).round(2)
        cpa_values = cpa_values.replace([np.inf, -np.inf], np.nan)
        result['CPA'] = cpa_values.apply(lambda x: f"¥{x}" if pd.notna(x) else "")

    # 重新排列列顺序：维度 -> 数据行数 -> 其他指标
    # 按照原始顺序排列所有列
    all_numeric_cols = existing_sum_cols + existing_ratio_cols
    cols = [dimension, '数据行数'] + all_numeric_cols
    result = result[[col for col in cols if col in result.columns]]

    return result


def aggregate_cross(
    df: pd.DataFrame,
    dim_row: str,
    dim_col: str,
    metric: str,
    filters: Optional[Dict[str, List]] = None
) -> pd.DataFrame:
    """
    交叉维度聚合（生成透视表）

    参数:
        df (pd.DataFrame): 数据源DataFrame
        dim_row (str): 行维度（'parent_code' | 'pattern' | 'attribute'）
        dim_col (str): 列维度（'parent_code' | 'pattern' | 'attribute'）
        metric (str): 聚合指标（如'花费', '销售额', 'ROAS'等）
        filters (dict, optional): 筛选条件，格式如：
            {
                'parent_code': ['City', 'Flower'],
                'attribute': ['aesthetic']
            }
            如果为None表示不筛选

    返回:
        pd.DataFrame: 透视表（行维度 × 列维度）

    异常:
        AssertionError: 如果dim_row == dim_col
        ValueError: 如果metric不在DataFrame中
    """
    assert dim_row != dim_col, "行维度和列维度不能相同"

    if metric not in df.columns:
        raise ValueError(f"指标'{metric}'不在DataFrame中")

    # 复制数据（避免修改原DataFrame）
    filtered_df = df.copy()

    # 应用筛选条件
    if filters:
        for dim, values in filters.items():
            if values:  # 只在values非空时才筛选
                filtered_df = filtered_df[filtered_df[dim].isin(values)]

    # 先将指标列转换为数值类型
    filtered_df_copy = filtered_df.copy()
    filtered_df_copy[metric] = pd.to_numeric(filtered_df_copy[metric], errors='coerce')

    # 创建透视表
    pivot = pd.pivot_table(
        filtered_df_copy,
        values=metric,
        index=dim_row,
        columns=dim_col,
        aggfunc='sum',
        fill_value=np.nan,
        margins=True,
        margins_name='总计'
    )

    # 将0替换为NaN（便于显示为--）
    pivot = pivot.replace(0, np.nan)

    return pivot


def merge_pivots(pivot_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    合并多个透视表为一个表格

    将多个指标的透视表合并为一个表格，每列维度值下包含多个指标子列。

    参数:
        pivot_dict (dict): {指标名: 透视表DataFrame, ...}
            例如：{
                '花费': pivot_table_1,
                '销售额': pivot_table_2,
                'ROAS': pivot_table_3
            }

    返回:
        pd.DataFrame: 合并后的表格（MultiIndex列）

    示例输出结构:
        Parent Code | aesthetic_花费 | aesthetic_销售额 | collage_花费 | ... | 总计_花费 | ...
        -----------|-----------------|------------------|-------------|-----|----------|-----
        City       |     450         |      1200        |   280.5     | ... |    821   | ...
    """
    if not pivot_dict:
        raise ValueError("pivot_dict不能为空")

    # 合并所有透视表
    result = None
    for metric, pivot in pivot_dict.items():
        # 重命名列：原列名 -> 原列名_指标名（包括总计列）
        pivot_renamed = pivot.copy()
        pivot_renamed.columns = [f"{col}_{metric}" for col in pivot.columns]

        if result is None:
            result = pivot_renamed
        else:
            # 使用concat替代join，避免重复列名冲突
            result = pd.concat([result, pivot_renamed], axis=1)

    return result


def aggregate_cross_multi_metrics(
    df: pd.DataFrame,
    dim_row: str,
    dim_col: str,
    metrics: List[str],
    filters: Optional[Dict[str, List]] = None
) -> pd.DataFrame:
    """
    交叉分析：同时显示多个指标

    为多个指标分别创建透视表，然后合并为一个表格。

    参数:
        df (pd.DataFrame): 数据源
        dim_row (str): 行维度
        dim_col (str): 列维度
        metrics (list): 指标列表，如['花费', '销售额', 'ROAS']
        filters (dict, optional): 筛选条件

    返回:
        pd.DataFrame: 合并后的多指标透视表

    异常:
        ValueError: 如果metrics为空或所有指标都无效
    """
    if not metrics:
        raise ValueError("metrics不能为空")

    # 过滤有效的指标（必须存在于DataFrame中）
    valid_metrics = [m for m in metrics if m in df.columns]

    if not valid_metrics:
        raise ValueError(f"所有指标都不在DataFrame中，可用指标：{df.columns.tolist()}")

    # 为每个指标创建透视表
    pivot_dict = {}
    for metric in valid_metrics:
        pivot = aggregate_cross(df, dim_row, dim_col, metric, filters)
        pivot_dict[metric] = pivot

    # 合并所有透视表
    result = merge_pivots(pivot_dict)

    return result


def get_dimension_summary(df: pd.DataFrame) -> Dict:
    """
    获取数据的维度摘要信息

    参数:
        df (pd.DataFrame): 已提取维度的DataFrame

    返回:
        dict: {
            'total_rows': int,           # 总行数
            'parent_codes': dict,        # {'count': int, 'values': list}
            'patterns': dict,            # {'count': int, 'values': list}
            'attributes': dict,          # {'count': int, 'values': list}
            'invalid_count': int         # 异常数据行数
        }
    """
    return {
        'total_rows': len(df),
        'parent_codes': {
            'count': df['parent_code'].nunique(),
            'values': sorted(df['parent_code'].unique().tolist())
        },
        'patterns': {
            'count': df['pattern'].nunique(),
            'values': sorted(df['pattern'].unique().tolist())
        },
        'attributes': {
            'count': df['attribute'].nunique(),
            'values': sorted(df['attribute'].unique().tolist())
        },
        'invalid_count': (~df['is_valid']).sum()
    }
