import os
import numpy as np
import rasterio
from tqdm import tqdm

# 输入目录
CHV_DIR = r'D:\背景值处理_2m\CHV_2m'

# 获取所有CHV文件
chv_files = [f for f in os.listdir(CHV_DIR) if f.endswith('.tif') and not f.startswith('CHV_STMs_0506_maximum.tif')]

# 分析每个文件
total_files = len(chv_files)
print(f"共找到 {total_files} 个CHV文件\n")

# 设置显示格式
np.set_printoptions(precision=2, suppress=True)

for i, filename in enumerate(chv_files[:5], 1):  # 只分析前5个文件
    print(f"=== 分析文件 {i}/{total_files}: {filename} ===")
    file_path = os.path.join(CHV_DIR, filename)
    
    try:
        with rasterio.open(file_path) as src:
            # 获取基本信息
            height, width = src.shape
            count = src.count
            dtype = src.dtypes[0]
            nodata = src.nodatavals[0]
            
            print(f"  尺寸: {height}x{width}")
            print(f"  波段数: {count}")
            print(f"  数据类型: {dtype}")
            print(f"  NoData值: {nodata}")
            
            # 读取数据
            data = src.read(1)
            
            # 计算统计信息
            valid_data = data[~np.isnan(data)]
            
            if len(valid_data) == 0:
                print("  警告: 没有有效数据")
                continue
            
            # 基本统计
            min_val = np.min(valid_data)
            max_val = np.max(valid_data)
            mean_val = np.mean(valid_data)
            std_val = np.std(valid_data)
            median_val = np.median(valid_data)
            
            # 百分位数
            p10 = np.percentile(valid_data, 10)
            p25 = np.percentile(valid_data, 25)
            p50 = np.percentile(valid_data, 50)
            p75 = np.percentile(valid_data, 75)
            p90 = np.percentile(valid_data, 90)
            
            # 有效像素比例
            valid_ratio = len(valid_data) / (height * width) * 100
            
            print(f"  有效像素比例: {valid_ratio:.2f}%")
            print(f"  最小值: {min_val:.4f}")
            print(f"  最大值: {max_val:.4f}")
            print(f"  平均值: {mean_val:.4f}")
            print(f"  标准差: {std_val:.4f}")
            print(f"  中位数: {median_val:.4f}")
            print(f"  百分位数 [10%: {p10:.4f}, 25%: {p25:.4f}, 50%: {p50:.4f}, 75%: {p75:.4f}, 90%: {p90:.4f}]")
            
            # 检查数据是否合理
            print(f"  数据范围: [{min_val:.2f}, {max_val:.2f}]")
            if max_val - min_val < 0.0001:
                print("  警告: 数据范围非常小，可能存在问题")
            elif mean_val < 0:
                print("  注意: 平均值为负")
            
            print()
            
    except Exception as e:
        print(f"  错误: {str(e)}")
        print()

# 检查有问题的文件
print("=== 检查问题文件 ===")
problem_file = os.path.join(CHV_DIR, 'CHV_STMs_0506_maximum.tif')
if os.path.exists(problem_file):
    size = os.path.getsize(problem_file)
    print(f"文件 {os.path.basename(problem_file)} 大小为 {size} 字节")
    if size == 0:
        print("该文件是空的，可能生成过程中出现了错误")
