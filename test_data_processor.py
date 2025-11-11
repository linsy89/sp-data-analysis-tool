"""
数据处理模块的单元测试

运行方式：
    pytest test_data_processor.py -v
    pytest test_data_processor.py --cov=data_processor
"""

import pytest
import pandas as pd
import numpy as np
from data_processor import (
    extract_dimensions,
    extract_all_dimensions,
    validate_excel,
    aggregate_single,
    aggregate_cross,
    aggregate_cross_multi_metrics,
    get_dimension_summary
)


class TestExtractDimensions:
    """测试extract_dimensions函数"""

    def test_normal_case(self):
        """正常情况：所有维度都能提取"""
        result = extract_dimensions("City-LightballsCollage-IP15 aesthetic")
        assert result['parent_code'] == 'City'
        assert result['pattern'] == 'LightballsCollage'
        assert result['attribute'] == 'aesthetic'
        assert result['is_valid'] == True

    def test_missing_hyphen(self):
        """缺少"-"的情况"""
        result = extract_dimensions("NoHyphen aesthetic")
        assert result['parent_code'] == '未分类'
        assert result['pattern'] == '未分类'
        assert result['attribute'] == 'aesthetic'
        assert result['is_valid'] == True  # 因为有属性，所以有效

    def test_missing_space(self):
        """缺少空格的情况"""
        result = extract_dimensions("City-Pattern")
        assert result['parent_code'] == 'City'
        assert result['pattern'] == 'Pattern'
        assert result['attribute'] == '未分类'
        assert result['is_valid'] == True

    def test_only_parent_code(self):
        """只有Parent Code"""
        result = extract_dimensions("City-")
        assert result['parent_code'] == 'City'
        assert result['pattern'] == '未分类'
        assert result['attribute'] == '未分类'
        assert result['is_valid'] == True

    def test_none_input(self):
        """None输入"""
        result = extract_dimensions(None)
        assert result['is_valid'] == False
        assert result['parent_code'] == '未分类'

    def test_empty_string(self):
        """空字符串输入"""
        result = extract_dimensions("")
        assert result['is_valid'] == False

    def test_whitespace_only(self):
        """只有空格的字符串"""
        result = extract_dimensions("   ")
        assert result['is_valid'] == False

    def test_with_extra_hyphens(self):
        """多于两个"-"的情况"""
        result = extract_dimensions("City-Pattern-Extra-Hyphens value")
        assert result['parent_code'] == 'City'
        assert result['pattern'] == 'Pattern'
        assert result['attribute'] == 'value'

    def test_chinese_attribute(self):
        """包含中文属性"""
        result = extract_dimensions("Flower-FloralSky-IP15 人群 ip15")
        assert result['parent_code'] == 'Flower'
        assert result['pattern'] == 'FloralSky'
        assert result['attribute'] == '人群'  # 只取第一个空格后的第一个单词

    def test_numeric_parent_code(self):
        """包含数字的Parent Code"""
        result = extract_dimensions("SunFlower1-IP16-AI关键词")
        assert result['parent_code'] == 'SunFlower1'
        assert result['pattern'] == 'IP16'


class TestExtractAllDimensions:
    """测试extract_all_dimensions函数"""

    @pytest.fixture
    def test_data(self):
        """创建测试数据"""
        return pd.DataFrame({
            '广告活动': [
                'City-LightballsCollage-IP15 aesthetic',
                'Flower-FloralSky-IP15 人群 ip15',
                'NoHyphen value',
                None,
                'City-Pattern',
                '--',
            ],
            '花费': [100, 200, 150, 300, 120, 180],
            '销售额': [300, 450, 280, 800, 200, 400],
        })

    def test_extract_adds_columns(self, test_data):
        """检查是否添加了4个新列"""
        result = extract_all_dimensions(test_data)

        assert 'parent_code' in result.columns
        assert 'pattern' in result.columns
        assert 'attribute' in result.columns
        assert 'is_valid' in result.columns

    def test_extract_preserves_original_data(self, test_data):
        """检查是否保留了原始列"""
        result = extract_all_dimensions(test_data)

        assert '广告活动' in result.columns
        assert '花费' in result.columns
        assert '销售额' in result.columns
        assert len(result) == len(test_data)

    def test_extract_data_accuracy(self, test_data):
        """检查提取数据的准确性"""
        result = extract_all_dimensions(test_data)

        # 第一行
        assert result.loc[0, 'parent_code'] == 'City'
        assert result.loc[0, 'attribute'] == 'aesthetic'

        # 第二行（中文属性）
        assert result.loc[1, 'parent_code'] == 'Flower'
        assert result.loc[1, 'attribute'] == '人群'  # 只取第一个单词

        # 第三行（缺少"-"）
        assert result.loc[2, 'parent_code'] == '未分类'
        assert result.loc[2, 'pattern'] == '未分类'
        assert result.loc[2, 'attribute'] == 'value'

    def test_missing_campaign_column(self):
        """测试缺少'广告活动'列的异常"""
        df = pd.DataFrame({
            '其他列': [1, 2, 3]
        })

        with pytest.raises(KeyError):
            extract_all_dimensions(df)

    def test_empty_dataframe(self):
        """测试空DataFrame"""
        df = pd.DataFrame({'广告活动': []})
        result = extract_all_dimensions(df)

        assert len(result) == 0
        assert 'parent_code' in result.columns


class TestValidateExcel:
    """测试validate_excel函数"""

    def test_valid_excel(self):
        """有效的Excel数据"""
        df = pd.DataFrame({
            '广告活动': ['City-Pattern value', 'Flower-Sky attr'],
            '花费': [100, 200],
            '销售额': [300, 400]
        })

        result = validate_excel(df)
        assert result['valid'] == True
        assert len(result['errors']) == 0

    def test_missing_campaign_column(self):
        """缺少'广告活动'列"""
        df = pd.DataFrame({
            '其他列': [1, 2]
        })

        result = validate_excel(df)
        assert result['valid'] == False
        assert len(result['errors']) > 0

    def test_empty_dataframe(self):
        """空DataFrame"""
        df = pd.DataFrame()

        result = validate_excel(df)
        assert result['valid'] == False

    def test_missing_numeric_columns(self):
        """缺少数值列"""
        df = pd.DataFrame({
            '广告活动': ['City-Pattern value']
        })

        result = validate_excel(df)
        assert result['valid'] == True  # 有'广告活动'就有效
        assert len(result['warnings']) > 0  # 但有警告


class TestAggregateSingle:
    """测试aggregate_single函数"""

    @pytest.fixture
    def test_data(self):
        """创建测试数据"""
        df = pd.DataFrame({
            'parent_code': ['City', 'City', 'Flower', 'Flower'],
            'pattern': ['Blue', 'Blue', 'Red', 'Sky'],
            'attribute': ['A', 'A', 'B', 'B'],
            '花费': [100, 150, 200, 250],
            '销售额': [300, 400, 500, 600],
            'ROAS': [3.0, 2.67, 2.5, 2.4]
        })
        return df

    def test_aggregate_by_parent_code(self, test_data):
        """按Parent Code聚合"""
        result = aggregate_single(test_data, 'parent_code')

        assert len(result) == 2
        assert 'City' in result['parent_code'].values
        assert 'Flower' in result['parent_code'].values

    def test_aggregate_values_correct(self, test_data):
        """验证聚合值准确"""
        result = aggregate_single(test_data, 'parent_code')

        city_row = result[result['parent_code'] == 'City'].iloc[0]
        assert city_row['花费'] == 250  # 100 + 150
        assert city_row['销售额'] == 700  # 300 + 400
        assert city_row['数据行数'] == 2

    def test_aggregate_by_pattern(self, test_data):
        """按图案聚合"""
        result = aggregate_single(test_data, 'pattern')
        assert len(result) == 3

    def test_aggregate_by_attribute(self, test_data):
        """按属性聚合"""
        result = aggregate_single(test_data, 'attribute')
        assert len(result) == 2

    def test_invalid_dimension(self, test_data):
        """无效的维度参数"""
        with pytest.raises(ValueError):
            aggregate_single(test_data, 'invalid_dim')


class TestAggregateCross:
    """测试aggregate_cross函数"""

    @pytest.fixture
    def test_data(self):
        """创建测试数据"""
        df = pd.DataFrame({
            'parent_code': ['City', 'City', 'City', 'Flower', 'Flower'],
            'attribute': ['A', 'B', 'B', 'A', 'B'],
            '花费': [100, 150, 200, 250, 300]
        })
        return df

    def test_cross_analysis_basic(self, test_data):
        """基础交叉分析"""
        result = aggregate_cross(test_data, 'parent_code', 'attribute', '花费')

        # 应该有2行（City, Flower）+ 1行总计
        assert len(result) == 3
        # 应该有2列（A, B）+ 1列总计
        assert len(result.columns) == 3

    def test_cross_analysis_dimensions_different(self, test_data):
        """行列维度不能相同"""
        with pytest.raises(AssertionError):
            aggregate_cross(test_data, 'parent_code', 'parent_code', '花费')

    def test_cross_analysis_with_filter(self, test_data):
        """带筛选条件的交叉分析"""
        filters = {'parent_code': ['City']}
        result = aggregate_cross(test_data, 'parent_code', 'attribute', '花费', filters)

        # 筛选后应该只有City
        assert 'City' in result.index
        assert 'Flower' not in result.index

    def test_cross_analysis_invalid_metric(self, test_data):
        """无效的指标"""
        with pytest.raises(ValueError):
            aggregate_cross(test_data, 'parent_code', 'attribute', '不存在的指标')


class TestAggregateMultiMetrics:
    """测试aggregate_cross_multi_metrics函数"""

    @pytest.fixture
    def test_data(self):
        """创建测试数据"""
        df = pd.DataFrame({
            'parent_code': ['City', 'City', 'Flower', 'Flower'],
            'attribute': ['A', 'B', 'A', 'B'],
            '花费': [100, 150, 200, 250],
            '销售额': [300, 400, 500, 600],
            'ROAS': [3.0, 2.67, 2.5, 2.4]
        })
        return df

    def test_multi_metrics(self, test_data):
        """多指标聚合"""
        metrics = ['花费', '销售额', 'ROAS']
        result = aggregate_cross_multi_metrics(
            test_data, 'parent_code', 'attribute', metrics
        )

        assert result.shape[0] > 0
        assert result.shape[1] > 0

    def test_multi_metrics_empty_list(self, test_data):
        """空指标列表"""
        with pytest.raises(ValueError):
            aggregate_cross_multi_metrics(test_data, 'parent_code', 'attribute', [])


class TestDimensionSummary:
    """测试get_dimension_summary函数"""

    @pytest.fixture
    def test_data(self):
        """创建测试数据"""
        df = pd.DataFrame({
            'parent_code': ['City', 'City', 'Flower', 'Peach'],
            'pattern': ['Blue', 'Blue', 'Red', 'Red'],
            'attribute': ['A', 'B', 'A', 'B'],
            'is_valid': [True, True, True, False]
        })
        return df

    def test_summary_structure(self, test_data):
        """检查摘要结构"""
        summary = get_dimension_summary(test_data)

        assert 'total_rows' in summary
        assert 'parent_codes' in summary
        assert 'patterns' in summary
        assert 'attributes' in summary
        assert 'invalid_count' in summary

    def test_summary_values(self, test_data):
        """检查摘要值"""
        summary = get_dimension_summary(test_data)

        assert summary['total_rows'] == 4
        assert summary['parent_codes']['count'] == 3
        assert summary['patterns']['count'] == 2
        assert summary['attributes']['count'] == 2
        assert summary['invalid_count'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
