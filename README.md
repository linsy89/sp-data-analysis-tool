# SP 广告数据分析工具

一个用于 SP 广告数据维度提取和多维度分析的 Streamlit Web 应用。

## 功能特性

✅ **维度提取**
- 自动从广告活动名称提取 3 个维度
  - Parent Code（第一个 `-` 之前）
  - 图案（第一个和第二个 `-` 之间）
  - 属性（第一个空格之后的第一个单词）

✅ **单维度分析**
- 按 Parent Code、图案或属性分组统计
- 支持多个聚合指标（花费、销售额、ROAS 等）

✅ **交叉分析**
- 支持两个维度的交叉透视
- 同时显示多个指标
- 支持自定义筛选条件

✅ **数据导出**
- 导出结果为 Excel 文件
- 包含原始数据、聚合结果、交叉分析等多个工作表

## 项目结构

```
├── app.py                    # Streamlit Web 应用主文件
├── data_processor.py         # 数据处理核心模块
├── test_data_processor.py    # 单元测试（32 个测试）
├── quick_analyze.py          # 命令行快速分析工具
├── requirements.txt          # Python 依赖
├── 验证分析.ipynb           # Jupyter Notebook 验证脚本
├── 需求修正说明.md          # 详细的需求和修正说明
└── README.md                 # 本文件
```

## 安装和运行

### 方式 1：本地运行

1. 克隆或下载此仓库
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 运行 Streamlit 应用：
   ```bash
   streamlit run app.py
   ```

4. 浏览器会自动打开 `http://localhost:8501`

### 方式 2：Replit 部署（推荐）

1. Fork 此仓库到 GitHub
2. 在 Replit 中导入 GitHub 仓库
3. Replit 会自动识别 `requirements.txt` 并安装依赖
4. 在 Replit Shell 中运行：
   ```bash
   streamlit run app.py --server.port=3000 --server.address=0.0.0.0
   ```

## 使用方式

1. **上传 Excel 文件**
   - 在左侧边栏选择 Excel 文件（支持 .xlsx 和 .xls）
   - 文件必须包含 `广告活动` 列

2. **查看数据提取结果**
   - 自动显示 4 个关键指标
   - 数据质量统计
   - 维度详情（可展开）
   - 样本数据和异常数据

3. **进行分析**
   - 单维度分析：按某个维度分组统计
   - 交叉分析：两个维度的透视分析
   - 支持按条件筛选

4. **导出结果**
   - 将分析结果导出为 Excel 文件
   - 包含多个工作表，便于查看和共享

## 数据格式要求

Excel 文件必须包含以下列：

- **广告活动列**（如 C 列）：包含形如 `City-LightballsCollage-IP15 aesthetic` 的数据
- **数值列**（可选）：花费、销售额、ROAS 等指标

### 广告活动名称格式示例

```
City-LightballsCollage-IP15 aesthetic
↓ 提取 ↓
Parent Code: City
图案: LightballsCollage
属性: aesthetic
```

## 核心模块说明

### data_processor.py

提供 7 个核心函数：

- `extract_dimensions(campaign_name)` - 从单个广告活动名称提取维度
- `extract_all_dimensions(df)` - 对整个 DataFrame 提取维度
- `validate_excel(df)` - 验证 Excel 数据有效性
- `aggregate_single(df, dimension)` - 按单个维度聚合
- `aggregate_cross(df, dim_row, dim_col, metric, filters)` - 创建透视表
- `aggregate_cross_multi_metrics(df, dim_row, dim_col, metrics, filters)` - 多指标交叉分析
- `get_dimension_summary(df)` - 获取维度摘要统计

### 测试

运行所有单元测试：
```bash
pytest test_data_processor.py -v
```

已验证 32 个测试场景，涵盖：
- 正常情况
- 边界情况（缺少特定字符）
- 错误情况（None、空字符串等）
- 数据类型转换
- 多语言支持（中英文）

## 版本历史

### v1.0.0 - 2025-11-11

✅ **第 1 阶段 - 后端数据处理**
- 数据提取模块完成
- 单元测试完成（32/32 通过）
- 真实数据验证完成

✅ **第 2 阶段 - Step 1：基础框架 + 文件上传**
- Streamlit Web 应用框架
- 文件上传功能
- 维度提取结果展示
- 数据质量指标显示

🚀 **进行中**
- Step 2：单维度分析界面
- Step 3：交叉分析界面
- Step 4：数据筛选功能
- Step 5：数据导出功能

## 技术栈

- **Python 3.9+**
- **Streamlit 1.12.0** - Web 框架
- **Pandas 2.0+** - 数据处理
- **Plotly** - 数据可视化
- **openpyxl** - Excel 文件处理
- **pytest** - 单元测试

## 已知限制

- 当前版本在 Python 3.9 下运行（NumPy 1.x 兼容性）
- 单个 Excel 文件大小建议不超过 10MB
- 交叉分析支持单个指标聚合

## 常见问题

**Q: 数据上传后没有反应？**
A: 请检查 Excel 文件是否包含 `广告活动` 列，且文件不为空。

**Q: 如何在 Replit 上运行？**
A: 在 Replit Shell 运行以下命令：
```bash
streamlit run app.py --server.port=3000 --server.address=0.0.0.0
```

**Q: 支持哪些 Excel 格式？**
A: 支持 .xlsx（推荐）和 .xls 格式。

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎提出 Issue 或 Pull Request。

---

**最后更新**：2025-11-11
