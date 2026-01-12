# CHV (Convex Hull Volume) 计算项目

## 版本信息
- **版本**: v1.0.0
- **更新日期**: 2026-01-12
- **Python版本**: 3.12

## 项目简介
本项目用于计算CHV（凸包体积）指标，基于论文《Mapping tree species diversity in temperate montane forests using sentinel-1 and sentinel-2 imagery》的方法。项目实现了多维数据的CHV计算，支持并行处理和极端值过滤，适用于遥感影像数据的生物多样性分析。

## 文件说明

### 1. 核心计算脚本
- **01_calculate_chv_time_parallel.py** - 主CHV计算脚本
  - 功能：针对多个时间点/时间段的多维数据并行计算CHV
  - 特点：
    - 多时间点/时间段并行处理
    - 分块串行处理（避免嵌套并行）
    - 自动处理nodata值
    - 极端值过滤（-2000到2000范围）
    - 进度显示
    - 临时文件管理

### 2. 数据处理脚本
- **02_pdf_to_text.py** - PDF论文转文本
  - 功能：将研究论文PDF转换为可搜索的文本格式
  - 输出：research_paper.txt

### 3. 数据分析脚本
- **03_analyze_stm_extremes.py** - STM数据极端值分析
  - 功能：分析STM原始数据中1000以上值的分布情况
  - 结果：识别异常值来源和比例

- **04_analyze_all_chv_files.py** - 批量CHV文件分析
  - 功能：分析所有生成的CHV文件的基本统计信息
  - 输出：CHV值范围、有效像素比例等

- **05_check_spatial_distribution.py** - 空间分布检查
  - 功能：检查原始数据与CHV结果的空间一致性
  - 验证：有效像素的空间分布是否匹配

- **06_check_chv_data.py** - CHV结果合理性检查
  - 功能：检查CHV计算结果的范围和合理性
  - 分析：极端值、异常值和统计分布

- **07_check_raw_data.py** - 原始数据质量检查
  - 功能：检查原始数据的基本信息和质量
  - 输出：数据维度、nodata值、统计信息等

## 使用方法

### 1. 准备工作
- 确保已安装Python 3.12
- 创建并激活虚拟环境：
  ```bash
  python -m venv .venv
  .venv\Scripts\activate
  ```
- 安装依赖：
  ```bash
  pip install numpy rasterio scipy tqdm pypdf
  ```

### 2. 主要使用流程

#### 2.1 论文阅读（可选）
```bash
python 02_pdf_to_text.py
# 生成research_paper.txt用于了解CHV计算方法
```

#### 2.2 原始数据检查
```bash
python 07_check_raw_data.py
# 检查原始数据质量
```

#### 2.3 运行CHV计算（核心步骤）
```bash
python 01_calculate_chv_time_parallel.py
# 并行计算多个时间点/时间段的CHV
# 输入：D:\背景值处理_2m\MTs和STMs文件夹
# 输出：D:\背景值处理_2m\CHV_2m文件夹
```

#### 2.4 结果分析
```bash
# 检查CHV结果合理性
python 06_check_chv_data.py

# 检查空间分布一致性
python 05_check_spatial_distribution.py

# 批量分析所有CHV文件
python 04_analyze_all_chv_files.py
```

#### 2.5 异常值分析
```bash
# 分析STM数据极端值
python 03_analyze_stm_extremes.py
```

## 核心算法说明

### CHV (Convex Hull Volume) 计算
CHV用于度量多维数据的异质性，计算方法如下：

1. **1D数据**（单个像素的多个指标）：
   - 使用最大值与最小值的差：`CHV = max(values) - min(values)`
   - 与ConvexHull.volume数学等价，计算效率更高

2. **多维数据**（多个像素的多个指标）：
   - 使用scipy.spatial.ConvexHull计算凸包体积
   - 表示多维数据的分散程度

### 数据处理流程
1. 读取原始数据（MTs和STMs）
2. 处理nodata值（-9999等转换为np.nan）
3. 极端值过滤（-2000到2000范围）
4. 分块并行计算CHV
5. 合并结果并保存为GeoTIFF文件

## 注意事项
- 确保输入数据路径正确（默认：D:\背景值处理_2m）
- 虚拟环境需使用Python 3.12
- 大数据量计算可能需要较长时间
- 计算过程中会显示实时进度

## 论文相关
- **论文标题**: Mapping tree species diversity in temperate montane forests using sentinel-1 and sentinel-2 imagery
- **作者**: Liu 等
- **年份**: 2023
- **主要方法**: 使用Sentinel-1和Sentinel-2影像计算CHV指标进行树种多样性制图

## 许可证
MIT License

---
**更新说明**：
- v1.0.0 (2026-01-12): 完成核心功能开发，优化并行策略，添加异常值处理
- 修复了嵌套并行导致脚本卡住的问题
- 实现了针对多时间点/时间段的并行处理
- 添加了极端值过滤机制
