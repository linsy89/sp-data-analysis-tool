"""
快速分析工具 - 用于快速验证数据提取和聚合结果

使用方式：
    python quick_analyze.py <Excel路径> [--export]

示例：
    python quick_analyze.py /path/to/data.xlsx
    python quick_analyze.py /path/to/data.xlsx --export

--export 参数会生成结果Excel文件
"""

import sys
import pandas as pd
from pathlib import Path
from data_processor import (
    extract_all_dimensions,
    validate_excel,
    aggregate_single,
    aggregate_cross_multi_metrics,
    get_dimension_summary
)


def print_section(title, char="="):
    """打印分隔线"""
    print(f"\n{char * 70}")
    print(f"  {title}")
    print(f"{char * 70}")


def analyze_file(excel_path, export=False):
    """分析Excel文件并展示结果"""

    excel_path = Path(excel_path)

    if not excel_path.exists():
        print(f"❌ 文件不存在：{excel_path}")
        return False

    print_section("📊 数据分析工具", "=")
    print(f"\n📁 文件：{excel_path.name}")

    try:
        # 读取Excel
        df = pd.read_excel(excel_path)
        print(f"✅ 读取成功")
        print(f"   - 行数：{len(df)}")
        print(f"   - 列数：{len(df.columns)}")

        # 验证数据
        validation = validate_excel(df)
        if not validation['valid']:
            print(f"\n❌ 数据验证失败：")
            for error in validation['errors']:
                print(f"   {error}")
            return False

        print(f"✅ 数据验证通过")

        # 提取维度
        print(f"\n⏳ 正在提取维度...")
        df_extracted = extract_all_dimensions(df)
        print(f"✅ 提取完成")

        # 获取统计
        summary = get_dimension_summary(df_extracted)

        print_section("📈 维度统计")
        print(f"\n总行数：{summary['total_rows']}")
        print(f"\n📍 Parent Code：{summary['parent_codes']['count']} 种")
        for i, code in enumerate(summary['parent_codes']['values'][:5], 1):
            print(f"   {i}. {code}")
        if len(summary['parent_codes']['values']) > 5:
            print(f"   ... 等共 {summary['parent_codes']['count']} 种")

        print(f"\n🎨 图案：{summary['patterns']['count']} 种")
        for i, pattern in enumerate(summary['patterns']['values'][:5], 1):
            print(f"   {i}. {pattern}")
        if len(summary['patterns']['values']) > 5:
            print(f"   ... 等共 {summary['patterns']['count']} 种")

        print(f"\n🏷️  属性：{summary['attributes']['count']} 种")
        for i, attr in enumerate(summary['attributes']['values'][:5], 1):
            print(f"   {i}. {attr}")
        if len(summary['attributes']['values']) > 5:
            print(f"   ... 等共 {summary['attributes']['count']} 种")

        print(f"\n⚠️  数据质量：")
        print(f"   - 有效数据：{summary['total_rows'] - summary['invalid_count']} 行 ({100*(summary['total_rows']-summary['invalid_count'])/summary['total_rows']:.1f}%)")
        print(f"   - 异常数据：{summary['invalid_count']} 行 ({100*summary['invalid_count']/summary['total_rows']:.1f}%)")

        # 聚合示例
        print_section("📊 聚合分析示例", "-")

        # 单维度聚合
        print(f"\n【示例1】按 Parent Code 聚合（花费和销售额）")
        result_single = aggregate_single(df_extracted, 'parent_code')

        # 只显示必要的列
        display_cols = ['parent_code', '数据行数', '花费', '销售额']
        display_cols = [c for c in display_cols if c in result_single.columns]

        result_single_sorted = result_single.sort_values('花费', ascending=False)
        print(result_single_sorted[display_cols].head(10).to_string(index=False))

        # 交叉分析示例
        print(f"\n\n【示例2】Parent Code × 属性（花费、销售额、ROAS 交叉分析）")
        try:
            metrics = ['花费', '销售额', 'ROAS']
            available_metrics = [m for m in metrics if m in df_extracted.columns]

            if len(available_metrics) > 0:
                result_cross = aggregate_cross_multi_metrics(
                    df_extracted,
                    'parent_code',
                    'attribute',
                    available_metrics[:2]  # 只显示前2个指标避免太宽
                )
                print(result_cross.head(10).to_string())
            else:
                print("（无可用指标）")
        except Exception as e:
            print(f"交叉分析示例错误：{e}")

        # 导出结果
        if export:
            print_section("💾 导出结果文件", "-")

            export_path = excel_path.parent / f"{excel_path.stem}_分析结果.xlsx"

            with pd.ExcelWriter(export_path, engine='openpyxl') as writer:
                # 工作表1：提取的维度
                df_extracted_display = df_extracted[[
                    '广告活动', 'parent_code', 'pattern', 'attribute', 'is_valid'
                ]].copy()
                df_extracted_display.to_excel(writer, sheet_name='提取的维度', index=False)

                # 工作表2：按Parent Code聚合
                result_single = aggregate_single(df_extracted, 'parent_code')
                result_single.sort_values('花费', ascending=False).to_excel(
                    writer, sheet_name='Parent Code 聚合', index=False
                )

                # 工作表3：按图案聚合
                result_pattern = aggregate_single(df_extracted, 'pattern')
                result_pattern.sort_values('花费', ascending=False).to_excel(
                    writer, sheet_name='图案聚合', index=False
                )

                # 工作表4：按属性聚合
                result_attr = aggregate_single(df_extracted, 'attribute')
                result_attr.sort_values('花费', ascending=False).head(50).to_excel(
                    writer, sheet_name='属性聚合(TOP50)', index=False
                )

                # 工作表5：统计摘要
                summary_df = pd.DataFrame({
                    '指标': ['总行数', '有效数据', '异常数据', 'Parent Code 种类', '图案种类', '属性种类'],
                    '数值': [
                        summary['total_rows'],
                        summary['total_rows'] - summary['invalid_count'],
                        summary['invalid_count'],
                        summary['parent_codes']['count'],
                        summary['patterns']['count'],
                        summary['attributes']['count']
                    ]
                })
                summary_df.to_excel(writer, sheet_name='统计摘要', index=False)

            print(f"\n✅ 已导出结果文件：")
            print(f"   {export_path}")
            print(f"\n   包含 5 个工作表：")
            print(f"   1. 提取的维度 - 原始数据+提取的3个维度")
            print(f"   2. Parent Code 聚合 - 按Parent Code的花费/销售额等汇总")
            print(f"   3. 图案聚合 - 按图案的汇总")
            print(f"   4. 属性聚合(TOP50) - 按属性的汇总（显示前50）")
            print(f"   5. 统计摘要 - 关键指标统计")

        print_section("✅ 分析完成", "=")
        return True

    except Exception as e:
        print(f"\n❌ 错误：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方式：")
        print("  python quick_analyze.py <Excel文件路径> [--export]")
        print("\n示例：")
        print("  python quick_analyze.py ~/Desktop/SP数据分析/data.xlsx")
        print("  python quick_analyze.py ~/Desktop/SP数据分析/data.xlsx --export")
        print("\n可选参数：")
        print("  --export  导出详细的Excel结果文件")
        sys.exit(1)

    excel_path = sys.argv[1]
    export = '--export' in sys.argv

    success = analyze_file(excel_path, export)
    sys.exit(0 if success else 1)
